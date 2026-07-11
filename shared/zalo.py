import os
import requests
import logging
import time

logger = logging.getLogger(__name__)

def send_zalo_message(messages: list[str] | str, dry_run: bool = False) -> bool:
    """Sends the formatted text messages to Zalo Bot API or prints to stdout in dry-run mode.
    Supports a single Chat ID or a comma-separated list of Chat IDs (e.g. 'id1,id2').
    """
    bot_token = os.environ.get("ZALO_BOT_TOKEN")
    chat_id_env = os.environ.get("ZALO_CHAT_ID")
    
    if isinstance(messages, str):
        msg_list = [messages]
    else:
        msg_list = messages
        
    if not chat_id_env:
        chat_ids = []
    else:
        chat_ids = [cid.strip() for cid in chat_id_env.split(",") if cid.strip()]
        
    if dry_run or not bot_token or not chat_ids:
        logger.info("--- DRY RUN / CONSOLE OUTPUT ---")
        for i, text in enumerate(msg_list, start=1):
            if len(msg_list) > 1:
                print(f"[Message Chunk {i}/{len(msg_list)}]")
            print(text)
            print()
        logger.info("--------------------------------")
        
        if not dry_run and (not bot_token or not chat_ids):
            logger.warning("ZALO_BOT_TOKEN or ZALO_CHAT_ID is missing. Defaulted to console print.")
        return True
        
    url = f"https://bot-api.zaloplatforms.com/bot{bot_token}/sendMessage"
    headers = {
        "Content-Type": "application/json"
    }
    
    overall_success = True
    for cid in chat_ids:
        logger.info(f"Sending message to Zalo chat_id: {cid}...")
        for i, text in enumerate(msg_list, start=1):
            if len(text) > 2000:
                logger.warning(f"Message chunk {i} length ({len(text)}) exceeds 2000 characters. Truncating to avoid Zalo error.")
                text = text[:1990] + "..."
                
            payload = {
                "chat_id": cid,
                "text": text
            }
            
            logger.info(f"Sending message chunk {i}/{len(msg_list)} to {cid}...")
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                response.raise_for_status()
                
                res_json = response.json()
                logger.info(f"Zalo API response for chunk {i} (to {cid}): {res_json}")
                
                if not res_json.get("ok"):
                    logger.error(f"Zalo API returned failure for {cid}: {res_json}")
                    overall_success = False
                    
                if i < len(msg_list):
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Failed to send Zalo message chunk {i} to {cid}: {e}")
                overall_success = False
                
    return overall_success
