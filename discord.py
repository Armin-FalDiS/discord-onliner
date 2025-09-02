import websocket
import time
import requests
import json
import os
import threading
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_user_configs():
    """Get all user configurations from environment variables"""
    configs = []
    i = 1
    
    while True:
        token = os.getenv(f"DISCORD_TOKEN_{i}")
        if not token or token == "YOUR_DISCORD_USER_TOKEN":
            break
            
        status = os.getenv(f"DISCORD_STATUS_{i}", "dnd")
        custom_status = os.getenv(f"DISCORD_CUSTOM_STATUS_{i}", "")
        
        configs.append({
            'token': token,
            'status': status,
            'custom_status': custom_status,
            'user_id': i
        })
        i += 1
    
    return configs

def get_user_info(token):
    """Get user information from Discord API"""
    headers = {"Authorization": token, "Content-Type": "application/json"}
    try:
        userinfo = requests.get('https://discordapp.com/api/v9/users/@me', headers=headers).json()
        username = userinfo.get("username", "Unknown")
        discriminator = userinfo.get("discriminator", "0000")
        userid = userinfo.get("id", "Unknown")
        return username, discriminator, userid
    except Exception as e:
        print(f"Error getting user info: {e}")
        return "Unknown", "0000", "Unknown"

def onliner(token, status, custom_status, user_id):
    """Main onliner function for a single user"""
    username, discriminator, userid = get_user_info(token)
    print(f"User {user_id}: Logged in as {username}#{discriminator} ({userid}).")
    
    while True:
        try:
            ws = websocket.WebSocket()
            ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
            start = json.loads(ws.recv())
            heartbeat = start["d"]["heartbeat_interval"]
            
            auth = {
                "op": 2,
                "d": {
                    "token": token,
                    "properties": {
                        "$os": "Windows 10",
                        "$browser": "Google Chrome",
                        "$device": "Windows",
                    },
                    "presence": {"status": status, "afk": False},
                },
                "s": None,
                "t": None,
            }
            ws.send(json.dumps(auth))
            
            # Only send custom status if one is specified
            if custom_status:
                cstatus = {
                    "op": 3,
                    "d": {
                        "since": 0,
                        "activities": [
                            {
                                "type": 4,
                                "state": custom_status,
                                "name": "Custom Status",
                                "id": "custom",
                            }
                        ],
                        "status": status,
                        "afk": False,
                    },
                }
                ws.send(json.dumps(cstatus))
            
            online = {"op": 1, "d": "None"}
            time.sleep(heartbeat / 1000)
            ws.send(json.dumps(online))
            
            # Keep connection alive
            while True:
                time.sleep(50)
                ws.send(json.dumps(online))
                
        except Exception as e:
            print(f"User {user_id} ({username}): Connection error: {e}")
            print(f"User {user_id} ({username}): Reconnecting in 5 seconds...")
            time.sleep(5)

def run_onliners():
    """Run onliners for all configured users"""
    configs = get_user_configs()
    
    if not configs:
        print("No Discord tokens configured. Please set DISCORD_TOKEN_1, DISCORD_TOKEN_2, etc.")
        print("Example: DISCORD_TOKEN_1=your_token_here")
        return
    
    print(f"Starting Discord onliner for {len(configs)} user(s)...")
    
    # Create and start threads for each user
    threads = []
    for config in configs:
        thread = threading.Thread(
            target=onliner,
            args=(config['token'], config['status'], config['custom_status'], config['user_id']),
            daemon=True
        )
        thread.start()
        threads.append(thread)
    
    # Wait for all threads to complete (they won't unless there's an error)
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\nShutting down Discord onliners...")

if __name__ == "__main__":
    run_onliners()
