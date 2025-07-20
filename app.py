from flask import Flask, request, jsonify
import requests, json, threading, time
from byte import Encrypt_ID, encrypt_api

app = Flask(__name__)
regions = ["bd"]

# 🔁 Auto Update Tokens Every 7 Hours
def update_tokens():
    while True:
        for region in regions:
            try:
                with open(f"accounts_{region}.json", "r") as file:
                    accounts = json.load(file)

                new_tokens = []
                for acc in accounts:
                    uid = acc["uid"]
                    password = acc["password"]
                    api_url = f"https://jwt-maker-ff.vercel.app/token?uid={uid}&password={password}"
                    try:
                        res = requests.get(api_url, timeout=10)
                        res_json = res.json()
                        if "token" in res_json:
                            new_tokens.append({"uid": uid, "token": res_json["token"]})
                    except Exception as e:
                        print(f"Token fetch failed for {uid}: {e}")

                with open(f"token_{region}.json", "w") as file:
                    json.dump(new_tokens, file, indent=4)

                print(f"[{region}] ✅ Tokens updated successfully")

            except Exception as e:
                print(f"Error updating tokens for {region}: {e}")

        # Wait 7 hours (25200 seconds)
        time.sleep(25200)

# Start token auto-updater in background
threading.Thread(target=update_tokens, daemon=True).start()

# 📤 Friend Request Sender
def send_friend_request(uid, region, token, results):
    encrypted_id = Encrypt_ID(uid)
    payload = f"08a7c4839f1e10{encrypted_id}1801"
    encrypted_payload = encrypt_api(payload)

    url = f"https://clientbp.ggblueshark.com/RequestAddingFriend"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Unity-Version": "2018.4.11f1",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; Android 9)",
    }

    try:
        res = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload))
        if res.status_code == 200:
            results["success"] += 1
        else:
            results["failed"] += 1
    except:
        results["failed"] += 1

# 🌐 /spam API Endpoint
@app.route("/spam", methods=["GET"])
def spam():
    uid = request.args.get("uid")
    key = request.args.get("key")

    if key != "GST_MODX":
        return jsonify({"error": "Invalid or missing API key 🔑"}), 403
    if not uid:
        return jsonify({"error": "uid parameter is required"}), 400

    tokens_with_region = []
    for region in regions:
        try:
            with open(f"token_{region}.json", "r") as file:
                data = json.load(file)
            tokens = [(region, item["token"]) for item in data]
            tokens_with_region.extend(tokens)
        except:
            continue

    if not tokens_with_region:
        return jsonify({"error": "No tokens found in any token file"}), 500

    results = {"success": 0, "failed": 0}
    threads = []

    for region, token in tokens_with_region[:100]:
        thread = threading.Thread(target=send_friend_request, args=(uid, region, token, results))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    status = 1 if results["success"] != 0 else 2
    return jsonify({
        "success_count": results["success"],
        "failed_count": results["failed"],
        "status": status,
        "telegram_channel": "@GHOST_XAPIS",
        "Contact_Developer": "@JOBAYAR_AHMED"
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5009)
