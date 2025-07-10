from flask import Flask, request, jsonify
import requests
import json
import time

from byte import Encrypt_ID, encrypt_api

app = Flask(__name__)

regions = ["bd"]

def load_tokens():
    all_tokens = []
    for region in regions:
        file_name = f"token_{region}.json"
        try:
            with open(file_name, "r") as file:
                data = json.load(file)
            tokens = [(region, item["token"]) for item in data]
            all_tokens.extend(tokens)
        except Exception as e:
            print(f"Error loading tokens from {file_name}: {e}")
    return all_tokens

def send_friend_request(uid, region, token):
    encrypted_id = Encrypt_ID(uid)
    payload = f"08a7c4839f1e10{encrypted_id}1801"
    encrypted_payload = encrypt_api(payload)

    url = "https://clientbp.ggblueshark.com/RequestAddingFriend"
    headers = {
        "Expect": "100-continue",
        "Authorization": f"Bearer {token}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB49",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "16",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-N975F Build/PI)",
        "Host": "clientbp.ggblueshark.com",
        "Connection": "close",
        "Accept-Encoding": "gzip, deflate, br"
    }

    try:
        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload))
        if response.status_code == 200:
            print(f"✅ Success: Request sent from token ({token[:10]}...)")
            return True
        else:
            print(f"❌ Failed: Token ({token[:10]}...) | Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending request with token ({token[:10]}...): {e}")
        return False

@app.route("/spam", methods=["GET"])
def spam_requests():
    uid = request.args.get("uid")
    key = request.args.get("key")

    if key != "GST_MODX":
        return jsonify({"error": "Invalid API Key"}), 403

    if not uid:
        return jsonify({"error": "Missing UID"}), 400

    tokens_with_region = load_tokens()
    if not tokens_with_region:
        return jsonify({"error": "No tokens found"}), 500

    success_count = 0
    fail_count = 0
    total_sent = 0

    print("🚀 স্প্যাম অপারেশন শুরু হয়েছে!")

    for region, token in tokens_with_region:
        ok = send_friend_request(uid, region, token)
        if ok:
            success_count += 1
        else:
            fail_count += 1
        total_sent += 1

        time.sleep(1.2)  # Detection এড়ানোর জন্য safe delay

    print("✅ সম্পূর্ণ স্প্যাম শেষ!")

    return jsonify({
        "success_count": success_count,
        "failed_count": fail_count,
        "total_requests_sent": total_sent,
        "uid": uid,
        "status": 1 if success_count > 0 else 2,
        "note": "All requests sent one-by-one to avoid detection & force notification delivery.",
        "Telegram": "@GHOST_XMOD",
        "Developer": "@JOBAYAR_AHMED"
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5009)
