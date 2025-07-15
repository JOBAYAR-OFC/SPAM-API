from flask import Flask, request, jsonify
import requests
import json
import time
import threading

from byte import Encrypt_ID, encrypt_api  # Ensure your encryption logic is inside byte.py

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
            print(f"[ERROR] Failed to load tokens from {file_name}: {e}")
    return all_tokens

def send_friend_request(uid, region, token, results, lock):
    try:
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

        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload))
        with lock:
            if response.status_code == 200:
                results["success"] += 1
            else:
                results["failed"] += 1
    except Exception as e:
        with lock:
            print(f"[FAILED] Token ({token[:10]}...): {e}")
            results["failed"] += 1

def spam_campaign(uid):
    tokens_with_region = load_tokens()
    results = {"success": 0, "failed": 0}
    results_lock = threading.Lock()

    batch_size = 3
    intra_delay = 0.05  # 50 milliseconds between requests
    inter_delay = 15    # 15 seconds between each batch

    total_sent = 0

    for i in range(0, len(tokens_with_region), batch_size):
        batch = tokens_with_region[i:i + batch_size]
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
                time.sleep(intra_delay)

        for thread in threads:
            thread.join()

        print(f"[BATCH COMPLETE] Success: {results['success']} | Failed: {results['failed']} | Total Sent: {total_sent}")

        if total_sent < len(tokens_with_region):
            print("[WAITING] Sleeping 15 seconds before next batch...")
            time.sleep(inter_delay)

    print("[DONE] Friend spam campaign completed!")

@app.route("/spam", methods=["GET"])
def spam_requests():
    uid = request.args.get("uid")
    key = request.args.get("key")

    if key != "GST_MODX":
        return jsonify({"error": "Invalid API Key"}), 403
    if not uid:
        return jsonify({"error": "Missing UID"}), 400

    # Start the spam campaign in background
    threading.Thread(target=spam_campaign, args=(uid,)).start()

    return jsonify({
        "status": 1,
        "message": "✅ Friend request spam started in the background!",
        "note": "Results will appear in console or log",
        "telegram": "@GHOST_XMOD",
        "developer": "@JOBAYAR_AHMED"
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5009)
