import sys
import os
import logging
import re
from datetime import datetime, timedelta, timezone

# Add project root to sys.path to allow importing from shared
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from shared.zalo import send_zalo_message

logger = logging.getLogger(__name__)

def format_message(data: dict) -> list[str]:
    """Formats the curated article JSON into a single structured text message."""
    title = data.get("title", "Bài đọc hôm nay")
    url = data.get("url", "")
    topic = data.get("topic", "General")
    
    # Get current date in Vietnam time (GMT+7)
    vn_date = datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y")
    
    vocab_list = data.get("vocab_words", [])
    phrases_list = data.get("phrases", [])
    
    vocab_str = "  • ".join(vocab_list)
    if vocab_str:
        vocab_str = f"• {vocab_str}"
        
    phrases_str = "\n".join(f"{i}. {phrase}" for i, phrase in enumerate(phrases_list, start=1))
    
    parts = [
        f"📚 BÀI ĐỌC TIẾNG ANH HÔM NAY - Ngày {vn_date}",
        f"🗂 Chủ đề: {topic}",
        f"🔗 {title} ({url})" if url else f"🔗 {title}",
        "",
        "🔤 New words:",
        vocab_str,
        "",
        "💬 Phrases:",
        phrases_str
    ]
    
    msg_text = "\n".join(parts)
    messages = [msg_text]
    
    story = data.get("story_passage", "")
    if story:
        story_msg = f"ĐOẠN VÍ DỤ\n\n{story}"
        messages.append(story_msg)
        
    return messages
