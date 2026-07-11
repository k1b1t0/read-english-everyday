from datetime import datetime, date, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

TOPICS = [
    {"name": "Science & Space", "slug": "science-space"},
    {"name": "Nature & Creative", "slug": "nature-creative"},
    {"name": "History, Culture & World", "slug": "history-culture-world"}
]

def get_current_topic() -> dict:
    """Calculates the current topic based on Vietnam day of week (GMT+7):
    - Mon (0), Tue (1) -> Science & Space
    - Wed (2), Thu (3) -> Nature & Creative
    - Fri (4), Sat (5), Sun (6) -> History, Culture & World
    """
    vn_now = datetime.now(timezone(timedelta(hours=7)))
    weekday = vn_now.weekday() # 0 is Monday, 6 is Sunday
    
    if weekday in (0, 1): # Monday, Tuesday
        topic = TOPICS[0]
    elif weekday in (2, 3): # Wednesday, Thursday
        topic = TOPICS[1]
    else: # Friday, Saturday, Sunday
        topic = TOPICS[2]
        
    logger.info(f"Vietnam Weekday: {weekday}. Current Topic Block: '{topic['name']}' (slug: '{topic['slug']}')")
    return topic

def get_this_week_topic() -> str:
    """Returns the current topic name."""
    return get_current_topic()["name"]
