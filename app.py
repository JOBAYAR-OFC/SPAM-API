from flask import Flask, request, jsonify
import requests
import json
import threading
import time # সময় বিরতির জন্য যোগ করা হয়েছে

# নিশ্চিত করুন এই মডিউলটি সঠিকভাবে ইমপ্লিমেন্ট করা আছে
from byte import Encrypt_ID, encrypt_api

app = Flask(__name__)

# Define the list of regions
regions = ["bd"]  # আপনার প্রয়োজন অনুযায়ী "sg", "br", ইত্যাদি যোগ করতে পারেন

# Load tokens for all regions
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
            # টোকেন ফাইল লোড করতে সমস্যা হলে কনসোলে ত্রুটি দেখাবে
            print(f"Error loading tokens from {file_name}: {e}")
    return all_tokens

# Function to send one friend request
# 'results' ডিকশনারিতে থ্রেড-সেফ অ্যাক্সেসের জন্য 'lock' প্যারামিটার যোগ করা হয়েছে
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
        # ফলাফলে পরিবর্তন করার আগে লক অর্জন করুন
        with lock:
            if response.status_code == 200:
                results["success"] += 1
            else:
                results["failed"] += 1
    except Exception as e:
        # ফলাফলে পরিবর্তন করার আগে লক অর্জন করুন
        with lock:
            print(f"Error sending request for region {region} with token {token}: {e}")
            results["failed"] += 1

# API endpoint with API key check
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

    # ফলাফলের জন্য থ্রেড-সেফ ডিকশনারি
    results = {"success": 0, "failed": 0}
    # ফলাফলে অ্যাক্সেস সিঙ্ক্রোনাইজ করতে একটি লক ব্যবহার করা হয়েছে
    results_lock = threading.Lock()

    # সর্বোচ্চ 100টি টোকেন ব্যবহার করুন
    tokens_to_use = tokens_with_region[:100]
    
    # মোট পাঠানো রিকোয়েস্ট ট্র্যাক করার জন্য একটি কাউন্টার
    total_requests_sent = 0

    print("স্প্যাম ক্যাম্পেইন শুরু হচ্ছে...")
    print("---")

    # প্রতিটি টোকেনের জন্য আলাদাভাবে রিকোয়েস্ট পাঠান এবং বিরতি দিন
    for region, token in tokens_to_use:
        thread = threading.Thread(target=send_friend_request, args=(uid, region, token, results, results_lock))
        thread.start()
        total_requests_sent += 1 # রিকোয়েস্ট শুরু হওয়ার সাথে সাথে কাউন্ট করুন

        # প্রতিটি রিকোয়েস্ট শুরু হওয়ার পর ২ মিলিসেকেন্ড অপেক্ষা করুন
        # শেষ রিকোয়েস্টের পর আর অপেক্ষা করার প্রয়োজন নেই
        if total_requests_sent < len(tokens_to_use):
            time.sleep(0.002) # 2 মিলিসেকেন্ড = 0.002 সেকেন্ড

        # এখানে থ্রেড.জয়েন() ব্যবহার করা হচ্ছে না কারণ আপনি চান রিকোয়েস্টগুলো দ্রুত পাঠানো হোক।
        # তবে, সব থ্রেড শেষ না হওয়া পর্যন্ত মূল থ্রেড (ফ্লাস্ক রিকোয়েস্ট) চলতে থাকবে।
        # যদি আপনি চান প্রতিটি রিকোয়েস্ট শেষ হওয়ার পরই কাউন্টার দেখতে,
        # তাহলে এখানে `thread.join()` দিতে হবে, কিন্তু সেটা আপনার 'আসতেই থাকে আসতেই থাকে' চাহিদার বিপরীত।
        # যেহেতু আপনি সম্পূর্ণ প্রক্রিয়া শেষে ফলাফল দেখতে চেয়েছেন, তাই আমরা এখানে অপেক্ষা করব না।
        # আপনি যদি প্রতিটি রিকোয়েস্ট শেষ হওয়ার পর পর্যায়ক্রমিক কাউন্ট দেখতে চান, তবে আপনাকে এটি বিবেচনা করতে হবে।

    # সব রিকোয়েস্ট শুরু হওয়ার পর, সব থ্রেড শেষ না হওয়া পর্যন্ত অপেক্ষা করুন
    # এটি নিশ্চিত করে যে সব রিকোয়েস্ট শেষ হওয়ার পরই চূড়ান্ত ফলাফল ফেরত দেওয়া হয়।
    for thread in threading.enumerate():
        if thread is not threading.current_thread():
            thread.join()


    print("---")
    print(f"সম্পূর্ণ ক্যাম্পেইন শেষ হয়েছে।")

    status = 1 if results["success"] != 0 else 2

    return jsonify({
        "success_count": results["success"],
        "failed_count": results["failed"],
        "status": status,
        "total_requests_sent": total_requests_sent, # মোট পাঠানো রিকোয়েস্ট ফলাফলে যোগ করা হয়েছে
        "telegram_channel": "@GHOST_XMOD",
        "Contact_Developer": "@JOBAYAR_AHMED"
    })

# Run Flask app
if __name__ == "__main__":
    # debug=True ডেভেলপমেন্টের জন্য ভালো, কিন্তু প্রোডাকশন এনভায়রনমেন্টের জন্য সুপারিশ করা হয় না
    app.run(debug=True, host="0.0.0.0", port=5009)
