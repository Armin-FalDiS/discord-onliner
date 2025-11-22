import websocket
import time
import requests
import json
import threading
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

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
            
            # Get start_hour and end_hour, validate them
            start_hour = account.get('start_hour')
            end_hour = account.get('end_hour')
            
            if start_hour is None or end_hour is None:
                logger.error(f"Account {idx}: Both start_hour and end_hour are required")
                continue
            
            try:
                start_hour = int(start_hour)
                end_hour = int(end_hour)
            except (ValueError, TypeError):
                logger.error(f"Account {idx}: start_hour and end_hour must be integers")
                continue
            
            if not (0 <= start_hour <= 23) or not (0 <= end_hour <= 23):
                logger.error(f"Account {idx}: start_hour and end_hour must be between 0 and 23")
                continue
            
            if start_hour >= end_hour:
                logger.error(f"Account {idx}: start_hour ({start_hour}) must be less than end_hour ({end_hour})")
                continue
            
            configs.append({
                'token': token,
                'status': status,
                'custom_status': custom_status,
                'start_hour': start_hour,
                'end_hour': end_hour,
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

def is_within_hours(current_hour, start_hour, end_hour):
    """Check if current hour is within the allowed time range"""
    return start_hour <= current_hour < end_hour

def wait_until_start_hour(start_hour, end_hour, user_id, username):
    """Wait until the start hour is reached"""
    while True:
        current_time = datetime.now()
        current_hour = current_time.hour
        
        # Check if we're now within allowed hours
        if is_within_hours(current_hour, start_hour, end_hour):
            break
        
        # Calculate target time (start_hour today or tomorrow)
        target_time = current_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        
        # If we're past end_hour or target_time is in the past, wait until tomorrow
        if current_hour >= end_hour or target_time <= current_time:
            target_time = target_time + timedelta(days=1)
        
        seconds_to_wait = (target_time - current_time).total_seconds()
        hours_to_wait = int(seconds_to_wait // 3600)
        minutes_to_wait = int((seconds_to_wait % 3600) // 60)
        logger.info(f"User {user_id} ({username}): Outside allowed hours (current: {current_hour}:00). Waiting until {start_hour}:00 ({hours_to_wait}h {minutes_to_wait}m)")
        time.sleep(min(seconds_to_wait, 3600))  # Sleep in 1-hour chunks to check periodically

def onliner(token, status, custom_status, start_hour, end_hour, user_id):
    """Main onliner function for a single user"""
    username, discriminator, userid = get_user_info(token)
    logger.info(f"User {user_id}: Logged in as {username}#{discriminator} ({userid}). Active hours: {start_hour}:00 - {end_hour}:00")
    
    while True:
        # Check if we're within allowed hours
        current_hour = datetime.now().hour
        if not is_within_hours(current_hour, start_hour, end_hour):
            wait_until_start_hour(start_hour, end_hour, user_id, username)
            continue
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
                # Check if we're still within allowed hours
                current_hour = datetime.now().hour
                if not is_within_hours(current_hour, start_hour, end_hour):
                    logger.info(f"User {user_id} ({username}): Outside allowed hours ({current_hour}:00). Disconnecting.")
                    ws.close()
                    break
                
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
            args=(config['token'], config['status'], config['custom_status'], 
                  config['start_hour'], config['end_hour'], config['user_id']),
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
