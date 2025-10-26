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
regions = ["bd", "ind"]  # Bangladesh and India regions

# Base URLs for different regions
region_base_urls = {
    "bd": "https://clientbp.ggblueshark.com",
    "ind": "https://client.ind.freefiremobile.com"
}

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

# Load tokens for specific region
def load_tokens(region):
    all_tokens = []
    file_name = f"token_{region}.json"
    try:
        with open(file_name, "r") as file:
            data = json.load(file)
        tokens = [(region, item["token"]) for item in data]
        all_tokens.extend(tokens)
    except Exception as e:
        print(f"Error loading tokens from {file_name}: {e}")
    return all_tokens

# Load all tokens for all regions
def load_all_tokens():
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

    url = f"{region_base_urls[region]}/RequestAddingFriend"
    headers = {
        "Expect": "100-continue",
        "Authorization": f"Bearer {token}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB50",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-N975F Build/PI)",
        "Host": url.split("//")[1].split("/")[0],
        "Connection": "close",
        "Accept-Encoding": "gzip, deflate, br"
    }

    try:
        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload))
        if response.status_code == 200:
            results["success"] += 1
            print(f"✅ Successfully sent friend request to {uid} using {region.upper()} token")
        else:
            results["failed"] += 1
            print(f"❌ Failed to send friend request to {uid} using {region.upper()} token - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error sending request for region {region} with token {token}: {e}")
        results["failed"] += 1

# API endpoint: /send_requests?uid={player_id}&region={region}
@app.route("/send_requests", methods=["GET"])
def send_requests():
    uid = request.args.get("uid")
    region = request.args.get("region", "all")  # Default to "all" if not specified

    if not uid:
        return jsonify({"error": "❌ uid parameter is required"}), 400

    # Validate region parameter
    if region != "all" and region not in regions:
        return jsonify({"error": f"❌ Invalid region. Available regions: {', '.join(regions)} or 'all'"}), 400

    # Load tokens based on region
    if region == "all":
        tokens_with_region = load_all_tokens()
    else:
        tokens_with_region = load_tokens(region)

    if not tokens_with_region:
        return jsonify({"error": f"❌ No tokens found for region: {region}"}), 500

    results = {"success": 0, "failed": 0}
    threads = []

    # Send using up to 100 tokens
    for reg, token in tokens_with_region[:100]:
        thread = threading.Thread(target=send_friend_request, args=(uid, reg, token, results))
        threads.append(thread)
        thread.start()
        time.sleep(0.1)  # Small delay to avoid rate limiting

    for thread in threads:
        thread.join()

    status = 1 if results["success"] != 0 else 2

    return jsonify({
        "success_count": results["success"],
        "failed_count": results["failed"],
        "status": status,
        "uid": uid,
        "region_used": region,
        "message": f"✅ Friend requests sent using {region.upper()} tokens",
        "available_regions": regions,
        "telegram_channel": "@GHOST_XAPIS",
        "Contact_Developer": "@JOBAYAR_AHMED"
    })

# API endpoint to get available regions
@app.route("/regions", methods=["GET"])
def get_regions():
    return jsonify({
        "available_regions": regions,
        "region_base_urls": region_base_urls
    })

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy", 
        "version": "2.0",
        "supported_regions": regions
    })

# Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
