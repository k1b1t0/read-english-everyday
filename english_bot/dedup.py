import os
import logging
import re

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_STATE_FILE = os.path.join(PROJECT_ROOT, "sent_urls.txt")

def normalize_url(url: str) -> str:
    """Normalizes News in Levels URLs by stripping out the '-level-X' suffix to avoid duplicates."""
    if not url:
        return ""
    # Strip whitespace, strip -level-X (case-insensitive), and strip trailing slash
    normalized = re.sub(r'(?i)-level-\d/?$', '', url.strip())
    if normalized.endswith('/'):
        normalized = normalized[:-1]
    return normalized

def load_sent_urls(filepath: str = None) -> set[str]:
    """Loads previously sent normalized URLs from the state file."""
    if filepath is None:
        filepath = DEFAULT_STATE_FILE
        
    if not os.path.exists(filepath):
        logger.info(f"State file {filepath} not found. Creating a new one.")
        return set()
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            urls = {normalize_url(line.strip()) for line in f if line.strip() and not line.strip().startswith("#")}
        logger.info(f"Loaded {len(urls)} normalized URLs from state file.")
        return urls
    except Exception as e:
        logger.error(f"Failed to read state file {filepath}: {e}")
        return set()

def add_sent_url(url: str, filepath: str = None, max_limit: int = 300) -> None:
    """Appends a new normalized URL to the state file and maintains the max limit."""
    if not url:
        return
        
    if filepath is None:
        filepath = DEFAULT_STATE_FILE
        
    normalized_url = normalize_url(url)
    try:
        # Load existing URLs in order of appearance
        ordered_urls = []
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        norm = normalize_url(stripped)
                        if norm not in ordered_urls:
                            ordered_urls.append(norm)
        
        # Append new URL if it isn't already in the list
        if normalized_url not in ordered_urls:
            ordered_urls.append(normalized_url)
            
        # Trim list to last max_limit entries
        if len(ordered_urls) > max_limit:
            ordered_urls = ordered_urls[-max_limit:]
            
        # Write back to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# Sent URLs list (normalized)\n")
            for item in ordered_urls:
                f.write(f"{item}\n")
                
        logger.info(f"Updated state file {filepath} with '{normalized_url}'. Total entries: {len(ordered_urls)}.")
    except Exception as e:
        logger.error(f"Failed to write state file {filepath}: {e}")
