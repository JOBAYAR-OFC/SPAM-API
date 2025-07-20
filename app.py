from flask import Flask, request, jsonify
import requests
import json
import threading
import time
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuration
TOKEN_REFRESH_HOURS = 7
API_KEY = "GST_MODX"  # Change this to your secret key
JWT_API_URL = "https://jwt-maker-ff.vercel.app/token"

# Data structure: {region: {"accounts": [(uid, password)], "tokens": [(token, expiry)], "last_refresh": datetime}}
account_data = {}
token_lock = threading.Lock()

def load_accounts():
    """Load accounts from accounts.json file"""
    global account_data
    try:
        with open("accounts.json", "r") as file:
            data = json.load(file)
            for region in data.get("regions", {}):
                account_data[region] = {
                    "accounts": [(acc["uid"], acc["password"]) for acc in data["regions"][region]],
                    "tokens": [],
                    "last_refresh": None
                }
        print("Accounts loaded successfully")
    except Exception as e:
        print(f"Error loading accounts: {e}")
        account_data = {"bd": {"accounts": [], "tokens": [], "last_refresh": None}}  # Default structure

def generate_token(uid, password):
    """Generate token using external API"""
    try:
        response = requests.get(f"{JWT_API_URL}?uid={uid}&password={password}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("token"), datetime.now() + timedelta(hours=TOKEN_REFRESH_HOURS)
        else:
            print(f"API Error: {response.status_code} for UID {uid}")
    except Exception as e:
        print(f"Error generating token for UID {uid}: {e}")
    return None, None

def refresh_tokens(region):
    """Refresh all tokens for a specific region"""
    if region not in account_data:
        return 0, 0
    
    generated = 0
    failed = 0
    new_tokens = []
    
    for uid, password in account_data[region]["accounts"]:
        token, expiry = generate_token(uid, password)
        if token:
            new_tokens.append((token, expiry))
            generated += 1
        else:
            failed += 1
    
    with token_lock:
        account_data[region]["tokens"] = new_tokens
        account_data[region]["last_refresh"] = datetime.now()
    
    return generated, failed

def get_active_tokens(region):
    """Get all active tokens for a region"""
    if region not in account_data:
        return []
    
    now = datetime.now()
    return [token for token, expiry in account_data[region]["tokens"] if expiry and expiry > now]

def start_token_refresher():
    """Background thread to periodically refresh tokens"""
    while True:
        time.sleep(TOKEN_REFRESH_HOURS * 3600)
        print("\nAuto-refreshing tokens...")
        for region in list(account_data.keys()):
            generated, failed = refresh_tokens(region)
            print(f"Region {region}: {generated} generated, {failed} failed")

# API Endpoints
@app.route("/token_status", methods=["GET"])
def token_status():
    key = request.args.get("key")
    if key != API_KEY:
        return jsonify({"error": "Invalid or missing API key 🔑"}), 403
    
    status_data = {}
    total_tokens = 0
    
    for region in account_data:
        active_tokens = get_active_tokens(region)
        last_refresh = account_data[region]["last_refresh"]
        
        if last_refresh:
            next_refresh = last_refresh + timedelta(hours=TOKEN_REFRESH_HOURS)
            remaining_time = next_refresh - datetime.now()
            remaining_hours = round(remaining_time.total_seconds() / 3600, 1)
            last_refresh_str = last_refresh.strftime("%Y-%m-%d %H:%M:%S")
            next_refresh_str = next_refresh.strftime("%Y-%m-%d %H:%M:%S")
        else:
            remaining_hours = 0
            last_refresh_str = "Never"
            next_refresh_str = "Now"
        
        status_data[region] = {
            "active_tokens": len(active_tokens),
            "accounts": len(account_data[region]["accounts"]),
            "last_refresh": last_refresh_str,
            "next_refresh": next_refresh_str,
            "remaining_hours": remaining_hours if remaining_hours > 0 else 0
        }
        total_tokens += len(active_tokens)
    
    return jsonify({
        "status": "success",
        "total_active_tokens": total_tokens,
        "regions": status_data,
        "refresh_interval_hours": TOKEN_REFRESH_HOURS,
        "telegram": "@GHOST_XAPIS",
        "developer": "@JOBAYAR_AHMED"
    })

@app.route("/refresh_tokens", methods=["GET"])
def manual_refresh():
    key = request.args.get("key")
    if key != API_KEY:
        return jsonify({"error": "Invalid or missing API key 🔑"}), 403
    
    results = {
        "total_generated": 0,
        "total_failed": 0,
        "region_details": {}
    }
    
    for region in list(account_data.keys()):
        generated, failed = refresh_tokens(region)
        active_tokens = get_active_tokens(region)
        
        results["region_details"][region] = {
            "tokens_generated": generated,
            "tokens_failed": failed,
            "total_active": len(active_tokens),
            "accounts": len(account_data[region]["accounts"])
        }
        results["total_generated"] += generated
        results["total_failed"] += failed
    
    return jsonify({
        "status": "Tokens refreshed successfully",
        "results": results,
        "telegram": "@GHOST_XAPIS",
        "developer": "@JOBAYAR_AHMED"
    })

@app.route("/spam", methods=["GET"])
def send_requests():
    uid = request.args.get("uid")
    key = request.args.get("key")

    if key != API_KEY:
        return jsonify({"error": "Invalid or missing API key 🔑"}), 403
    if not uid:
        return jsonify({"error": "uid parameter is required"}), 400
    
    results = {"success": 0, "failed": 0}
    threads = []
    
    for region in account_data:
        tokens = get_active_tokens(region)[:100]  # Limit to 100 tokens per region
        for token in tokens:
            thread = threading.Thread(target=send_friend_request, args=(uid, region, token, results))
            threads.append(thread)
            thread.start()
    
    for thread in threads:
        thread.join()
    
    status = "success" if results["success"] > 0 else "partial" if (results["success"] + results["failed"]) > 0 else "failed"
    return jsonify({
        "status": status,
        "success_count": results["success"],
        "failed_count": results["failed"],
        "total_attempts": results["success"] + results["failed"],
        "telegram": "@GHOST_XAPIS",
        "developer": "@JOBAYAR_AHMED"
    })

def send_friend_request(uid, region, token, results):
    try:
        # Your existing implementation here
        # ...
        # Simulate request for example:
        time.sleep(0.1)
        results["success"] += 1
    except Exception as e:
        print(f"Error: {e}")
        results["failed"] += 1

if __name__ == "__main__":
    # Initial setup
    load_accounts()
    
    # Start background refresher
    refresher_thread = threading.Thread(target=start_token_refresher)
    refresher_thread.daemon = True
    refresher_thread.start()
    
    # Run Flask app
    app.run(host="0.0.0.0", port=5009, debug=True)
