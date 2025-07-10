from flask import Flask, request, jsonify
import requests
import json
import time
import threading

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

def send_friend_request(uid, region, token, results, lock):
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
        with lock:
            if response.status_code == 200:
                results["success"] += 1
            else:
                results["failed"] += 1
    except Exception as e:
        with lock:
            print(f"❌ Error sending request with token ({token[:10]}...): {e}")
            results["failed"] += 1

@app.route("/spam", methods=["GET"])
def spam_requests():
    uid = request.args.get("uid")
    amount = request.args.get("amount", type=int)
    key = request.args.get("key")

    if key != "GST_MODX":
        return jsonify({"error": "Invalid API Key"}), 403
    if not uid:
        return jsonify({"error": "Missing UID"}), 400
    if not amount or amount <= 0:
        return jsonify({"error": "Amount must be a positive number"}), 400

    tokens_with_region = load_tokens()
    if not tokens_with_region:
        return jsonify({"error": "No tokens found"}), 500

    token_count = len(tokens_with_region)

    if amount > token_count:
        return jsonify({
            "error": "Not enough tokens",
            "tokens_available": token_count,
            "requested": amount,
            "max_possible": token_count
        }), 400

    # কাজের জন্য কাটা টোকেন
    usable_tokens = tokens_with_region[:amount]

    results = {"success": 0, "failed": 0}
    results_lock = threading.Lock()

    print(f"🚀 ক্যাম্পেইন শুরু হচ্ছে {amount} রিকুয়েস্ট পাঠানোর জন্য...")

    batch_size = 3
    intra_delay = 0.05  # ৫০ মিলিসেকেন্ড
    inter_delay = 15  # ব্যাচ শেষে ১৫ সেকেন্ড

    total_sent = 0

    for i in range(0, len(usable_tokens), batch_size):
        batch = usable_tokens[i:i + batch_size]
        threads = []

        for j, (region, token) in enumerate(batch):
            thread = threading.Thread(
                target=send_friend_request,
                args=(uid, region, token, results, results_lock)
            )
            threads.append(thread)
            thread.start()
            total_sent += 1
            if j < len(batch) - 1:
                time.sleep(intra_delay)  # ৫০ms delay

        for thread in threads:
            thread.join()

        print(f"📨 ব্যাচ শেষ: সফল={results['success']} ব্যর্থ={results['failed']} মোট={total_sent}")

        if total_sent < amount:
            print(f"⏳ ১৫ সেকেন্ড অপেক্ষা করা হচ্ছে পরবর্তী ব্যাচের জন্য...")
            time.sleep(inter_delay)

    print("🎉 স্প্যাম ক্যাম্পেইন সম্পূর্ণ!")

    return jsonify({
        "requested": amount,
        "success": results["success"],
        "failed": results["failed"],
        "tokens_used": total_sent,
        "status": 1 if results["success"] > 0 else 2,
        "note": "Request sent in 3-batch, 50ms intra-delay, 15s inter-batch for anti-detect",
        "telegram": "@GHOST_XMOD",
        "developer": "@JOBAYAR_AHMED"
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5009)
