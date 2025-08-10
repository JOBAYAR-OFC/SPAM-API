from flask import Flask, request, jsonify
import requests
import json
import threading
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii

app = Flask(__name__)

# Define the list of regions
regions = ["bd"]  # Add more like "sg", "br", etc., if needed

# Encryption functions
def encrypt_api(plain_text):
    plain_text = bytes.fromhex(plain_text)
    key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    cipher_text = cipher.encrypt(pad(plain_text, AES.block_size))
    return cipher_text.hex()

def Encrypt_ID(number):
    try:
        number = int(number)
        encoded_bytes = []
        while True:
            byte = number & 0x7F
            number >>= 7
            if number:
                byte |= 0x80
            encoded_bytes.append(byte)
            if not number:
                break
        return ''.join([f'{b:02x}' for b in encoded_bytes])
    except:
        return ""

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
            print(f"Error loading tokens from {file_name}: {e}")
    return all_tokens

# Function to send one friend request
def send_friend_request(uid, region, token, results):
    encrypted_id = Encrypt_ID(uid)
    payload = f"08a7c4839f1e10{encrypted_id}1801"
    encrypted_payload = encrypt_api(payload)

    url = f"https://clientbp.ggblueshark.com/RequestAddingFriend"
    headers = {
        "Expect": "100-continue",
        "Authorization": f"Bearer {token}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB50",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-N975F Build/PI)",
        "Host": "clientbp.ggblueshark.com",
        "Connection": "close",
        "Accept-Encoding": "gzip, deflate, br"
    }

    try:
        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload))
        if response.status_code == 200:
            results["success"] += 1
        else:
            results["failed"] += 1
    except Exception as e:
        print(f"Error sending request for region {region} with token {token}: {e}")
        results["failed"] += 1

# API endpoint: /send_requests?uid={player_id}
@app.route("/send_requests", methods=["GET"])
def send_requests():
    uid = request.args.get("uid")

    if not uid:
        return jsonify({"error": "❌ uid parameter is required"}), 400

    tokens_with_region = load_tokens()
    if not tokens_with_region:
        return jsonify({"error": "❌ No tokens found in any token file"}), 500

    results = {"success": 0, "failed": 0}
    threads = []
    MAX_THREADS = 50  # Maximum concurrent threads
    DELAY_BETWEEN_REQUESTS = 0.2  # Delay in seconds

    for region, token in tokens_with_region:
        # Wait if too many active threads
        while threading.active_count() > MAX_THREADS:
            time.sleep(0.1)
        
        thread = threading.Thread(target=send_friend_request, args=(uid, region, token, results))
        thread.start()
        threads.append(thread)
        time.sleep(DELAY_BETWEEN_REQUESTS)  # Rate limiting

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    status = 1 if results["success"] != 0 else 2

    return jsonify({
        "success_count": results["success"],
        "failed_count": results["failed"],
        "status": status,
        "uid": uid,
        "message": f"✅ Friend requests sent using {len(tokens_with_region)} tokens",
        "telegram_channel": "@GHOST_XAPIS",
        "Contact_Developer": "@JOBAYAR_AHMED"
    })

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "version": "1.0"})

# Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
