from flask import Flask, request, jsonify
import requests, json, threading, time
from byte import Encrypt_ID, encrypt_api

app = Flask(__name__)

ACCOUNTS_FILE = "accounts_bd.json"
TOKEN_FILE = "token_bd.json"

# 🔁 Auto Token Updater (every 7 hours)
def auto_update_tokens():
    while True:
        generate_tokens_and_save()
        time.sleep(25200)  # 7 hours

# 📦 Token generator function
def generate_tokens_and_save():
    try:
        with open(ACCOUNTS_FILE, "r") as f:
            accounts = json.load(f)

        new_tokens = []
        for acc in accounts:
            uid = acc["uid"]
            password = acc["password"]
            url = f"https://jwt-maker-ff.vercel.app/token?uid={uid}&password={password}"
            try:
                res = requests.get(url, timeout=10)
                data = res.json()
                if "token" in data:
                    new_tokens.append({"uid": uid, "token": data["token"]})
                    print(f"✅ Token generated for UID {uid}")
                else:
                    print(f"❌ Failed for UID {uid}: {data}")
            except Exception as e:
                print(f"❌ Error fetching token for {uid}: {e}")

        with open(TOKEN_FILE, "w") as f:
            json.dump(new_tokens, f, indent=4)

        return len(new_tokens)

    except Exception as e:
        print(f"❌ Error in generate_tokens_and_save: {e}")
        return 0

# 🧠 Start auto-updater thread
threading.Thread(target=auto_update_tokens, daemon=True).start()

# 🆕 /updatex route - manual token generator
@app.route("/updatex", methods=["GET"])
def manual_token_update():
    count = generate_tokens_and_save()
    return jsonify({
        "status": "success" if count > 0 else "failed",
        "total_tokens_created": count,
        "file_saved": TOKEN_FILE,
        "credit": "@JOBAYAR_AHMED",
        "channel": "@GHOST_XAPIS"
    })

# 📤 Friend Request Sender
def send_friend_request(target_uid, token, results):
    try:
        encrypted_id = Encrypt_ID(target_uid)
        payload = f"08a7c4839f1e10{encrypted_id}1801"
        encrypted_payload = encrypt_api(payload)

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Unity-Version": "2018.4.11f1",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0 (Linux; Android 9)",
        }

        url = "https://clientbp.ggblueshark.com/RequestAddingFriend"
        res = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload))

        if res.status_code == 200:
            results["success"] += 1
        else:
            results["failed"] += 1
    except:
        results["failed"] += 1

# 🌐 /spam endpoint
@app.route("/spam", methods=["GET"])
def spam():
    uid = request.args.get("uid")
    key = request.args.get("key")

    if key != "GST_MODX":
        return jsonify({"error": "Invalid or missing API key 🔑"}), 403
    if not uid:
        return jsonify({"error": "uid parameter is required"}), 400

    try:
        with open(TOKEN_FILE, "r") as file:
            tokens_data = json.load(file)

        results = {"success": 0, "failed": 0}
        threads = []

        for acc in tokens_data[:100]:
            token = acc.get("token")
            if token:
                thread = threading.Thread(target=send_friend_request, args=(uid, token, results))
                threads.append(thread)
                thread.start()

        for t in threads:
            t.join()

        return jsonify({
            "success_count": results["success"],
            "failed_count": results["failed"],
            "status": 1 if results["success"] > 0 else 2,
            "telegram_channel": "@GHOST_XAPIS",
            "Contact_Developer": "@JOBAYAR_AHMED"
        })

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500

# 🚀 Run app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5009)
