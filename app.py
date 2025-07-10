from flask import Flask, request, jsonify
import requests
import json
import threading
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

def send_friend_request(uid, region, token, results, lock):
    encrypted_id = Encrypt_ID(uid)
    payload = f"08a7c4839f1e10{encrypted_id}1801"
    encrypted_payload = encrypt_api(payload)

    url = f"https://clientbp.ggblueshark.com/RequestAddingFriend"
    headers = {
        "Expect": "100-continue",
        "Authorization": f"Bearer {token}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB49",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "16",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-N975F Build/PI)",
        "Host": f"clientbp.ggblueshark.com",
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
            print(f"Error sending request for region {region} with token {token}: {e}")
            results["failed"] += 1

@app.route("/spam", methods=["GET"])
def send_requests():
    uid = request.args.get("uid")
    key = request.args.get("key")

    if key != "GST_MODX":
        return jsonify({"error": "Invalid or missing API key 🔑"}), 403

    if not uid:
        return jsonify({"error": "uid parameter is required"}), 400

    tokens_with_region = load_tokens()
    if not tokens_with_region:
        return jsonify({"error": "No tokens found in any token file"}), 500

    results = {"success": 0, "failed": 0}
    results_lock = threading.Lock()

    tokens_to_use = tokens_with_region[:100]
    batch_size = 3
    intra_batch_delay = 0.005
    inter_batch_delay = 3
    
    total_requests_sent = 0

    print("স্প্যাম ক্যাম্পেইন শুরু হচ্ছে...")
    print("---")

    for i in range(0, len(tokens_to_use), batch_size):
        batch = tokens_to_use[i : i + batch_size]
        current_batch_threads = []

        for j, (region, token) in enumerate(batch):
            thread = threading.Thread(target=send_friend_request, args=(uid, region, token, results, results_lock))
            current_batch_threads.append(thread)
            thread.start()
            total_requests_sent += 1
            
            if j < len(batch) - 1:
                time.sleep(intra_batch_delay)

        for thread in current_batch_threads:
            thread.join()

        with results_lock:
            print(f"বর্তমান সফল রিকোয়েস্ট: {results['success']}, ব্যর্থ রিকোয়েস্ট: {results['failed']}, মোট পাঠানো রিকোয়েস্ট: {total_requests_sent}")

        if total_requests_sent < len(tokens_to_use):
            time.sleep(inter_batch_delay)

    print("---")
    print(f"সম্পূর্ণ ক্যাম্পেইন শেষ হয়েছে।")

    status = 1 if results["success"] != 0 else 2

    return jsonify({
        "success_count": results["success"],
        "failed_count": results["failed"],
        "status": status,
        "total_requests_sent": total_requests_sent,
        "telegram_channel": "@GHOST_XMOD",
        "Contact_Developer": "@JOBAYAR_AHMED"
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5009)
