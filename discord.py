import websocket
import time
import requests
import json
import threading
import logging
import sys
from pathlib import Path

# Configure logging to output to stdout with immediate flushing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Force stdout to be unbuffered for Docker logs
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

def get_user_configs():
    """Get all user configurations from JSON config file"""
    config_file = Path("config.json")
    
    if not config_file.exists():
        logger.error(f"Config file '{config_file}' not found. Please create it based on config.json.example")
        return []
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        accounts = config_data.get('accounts', [])
        if not accounts:
            logger.error("No accounts found in config.json")
            return []
        
        configs = []
        for idx, account in enumerate(accounts, start=1):
            token = account.get('token', '').strip()
            if not token or token == "YOUR_DISCORD_USER_TOKEN":
                logger.warning(f"Account {idx}: Skipping invalid or placeholder token")
                continue
            
            status = account.get('status', 'dnd')
            custom_status = account.get('custom_status', '')
            
            configs.append({
                'token': token,
                'status': status,
                'custom_status': custom_status,
                'user_id': idx
            })
        
        return configs
    
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config.json: {e}")
        return []
    except Exception as e:
        logger.error(f"Error reading config.json: {e}")
        return []

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
        logger.error(f"Error getting user info: {e}")
        return "Unknown", "0000", "Unknown"

def onliner(token, status, custom_status, user_id):
    """Main onliner function for a single user"""
    username, discriminator, userid = get_user_info(token)
    logger.info(f"User {user_id}: Logged in as {username}#{discriminator} ({userid}).")
    
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
            logger.error(f"User {user_id} ({username}): Connection error: {e}")
            logger.info(f"User {user_id} ({username}): Reconnecting in 5 seconds...")
            time.sleep(5)

def run_onliners():
    """Run onliners for all configured users"""
    configs = get_user_configs()
    
    if not configs:
        logger.error("No Discord accounts configured. Please check your config.json file.")
        logger.error("Example: See config.json.example for the expected format")
        return
    
    logger.info(f"Starting Discord onliner for {len(configs)} user(s)...")
    
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
        logger.info("\nShutting down Discord onliners...")

if __name__ == "__main__":
    logger.info("Discord Onliner starting up...")
    run_onliners()
