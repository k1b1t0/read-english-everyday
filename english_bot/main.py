import argparse
import sys
import os
import logging
from dotenv import load_dotenv

# Add project root and local directory to sys.path to make imports robust
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

local_path = os.path.dirname(os.path.abspath(__file__))
if local_path not in sys.path:
    sys.path.insert(0, local_path)

import feeds
import topic_rotation
import dedup
import curator
import notifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("english_bot")

def main():
    # Load .env file for local testing
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Daily English Learning Bot for Kids")
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Print the formatted message to console without calling Zalo API and without updating sent_urls.txt"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock curated article response instead of calling live Gemini API (useful for testing without keys)"
    )
    parser.add_argument(
        "--topic", 
        type=str, 
        help="Manually override the weekly topic (e.g. 'Space & Universe')"
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=100, 
        help="Max candidate articles to fetch from the RSS feed (default: 100)"
    )
    args = parser.parse_args()
    
    logger.info("Starting Daily English Bot pipeline...")
    
    # 1. Determine the topic
    if args.topic:
        weekly_topic = args.topic
        logger.info(f"Weekly topic overridden by command line argument: '{weekly_topic}'")
    else:
        topic_info = topic_rotation.get_current_topic()
        weekly_topic = topic_info["name"]
        
    # 2. Fetch RSS feed articles for the specific topic block
    all_articles = feeds.fetch_articles(topic_name=weekly_topic, max_items=args.limit)
    if not all_articles:
        logger.warning(f"No articles fetched for topic '{weekly_topic}'. Falling back to general feeds.")
        all_articles = feeds.fetch_articles(topic_name=None, max_items=args.limit)
        
    if not all_articles:
        logger.error("No articles fetched from any RSS feed. Pipeline execution aborted.")
        sys.exit(1)
        
    # 3. Filter out already sent URLs using deduplication
    sent_urls = dedup.load_sent_urls()
    candidates = [art for art in all_articles if dedup.normalize_url(art["url"]) not in sent_urls]
    
    logger.info(f"Filtered {len(all_articles)} articles down to {len(candidates)} unsent candidates.")
    
    # If topic feeds have no new articles, fall back to the general feed to find new content
    if not candidates:
        logger.warning("All articles in topic feeds have already been sent. Falling back to the general RSS feed to search for new content.")
        all_articles = feeds.fetch_articles(topic_name=None, max_items=args.limit)
        if all_articles:
            candidates = [art for art in all_articles if dedup.normalize_url(art["url"]) not in sent_urls]
            logger.info(f"Fallback to general feed: found {len(candidates)} unsent candidates.")
            
    # Ultimate fallback: if there are still absolutely no new articles anywhere, just reuse the general feed's latest articles
    if not candidates:
        logger.warning("All fetched articles in both topic and general feeds have already been sent in previous runs. Falling back to the latest general feed articles to avoid skipping delivery.")
        all_articles = feeds.fetch_articles(topic_name=None, max_items=args.limit)
        candidates = all_articles[:10] if all_articles else []
        
    if not candidates:
        logger.warning("No candidate articles available for curation. Sending generic fallback website list message.")
        import random
        from datetime import datetime, timezone, timedelta
        WEBSITES = [
            "https://newsforkids.net",
            "https://www.sciencejournalforkids.org",
            "https://www.smithsonianmag.com",
            "https://earthsky.org",
            "https://www.nasa.gov",
            "https://www.bbc.com/news",
            "https://learningenglish.voanews.com",
            "https://www.newsinlevels.com",
            "https://kidsactivitiesblog.com",
            "https://thekidshouldseethis.com"
        ]
        vn_date = datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y")
        selected_sites = random.sample(WEBSITES, 3)
        sites_str = "\n".join(f"• {site}" for site in selected_sites)
        fallback_msg = (
            f"📚 HỌC TIẾNG ANH HÔM NAY - Ngày {vn_date}\n\n"
            "Hôm nay hệ thống không tìm thấy bài viết mới nào phù hợp.\n"
            "Bạn hãy thử truy cập vào 3 trang web đọc tiếng Anh thú vị dưới đây nhé:\n\n"
            f"{sites_str}\n\n"
            "Chúc bạn học tập vui vẻ! ✨"
        )
        delivery_success = notifier.send_zalo_message(fallback_msg, dry_run=args.dry_run)
        if not delivery_success:
            logger.error("Failed to send generic fallback message via Zalo Bot API.")
            sys.exit(1)
        sys.exit(0)
        
    # 4. Generate curated article using Gemini
    curated_data = curator.curate_article(candidates, weekly_topic, mock=args.mock)
    
    if not curated_data:
        logger.warning("Gemini curation failed. Falling back to sending a random candidate article URL directly.")
        import random
        from datetime import datetime, timezone, timedelta
        selected_art = random.choice(candidates)
        vn_date = datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y")
        fallback_art_msg = (
            f"📚 BÀI ĐỌC TIẾNG ANH HÔM NAY - Ngày {vn_date}\n"
            f"🗂 Chủ đề: {weekly_topic}\n"
            f"🔗 {selected_art['title']} ({selected_art['url']})"
        )
        delivery_success = notifier.send_zalo_message(fallback_art_msg, dry_run=args.dry_run)
        if delivery_success:
            if not args.dry_run:
                dedup.add_sent_url(selected_art["url"])
                logger.info("Successfully sent fallback article message and updated state.")
            sys.exit(0)
        else:
            logger.error("Failed to send fallback article message. Falling back to generic website list message.")
            WEBSITES = [
                "https://newsforkids.net",
                "https://www.sciencejournalforkids.org",
                "https://www.smithsonianmag.com",
                "https://earthsky.org",
                "https://www.nasa.gov",
                "https://www.bbc.com/news",
                "https://learningenglish.voanews.com",
                "https://www.newsinlevels.com",
                "https://kidsactivitiesblog.com",
                "https://thekidshouldseethis.com"
            ]
            selected_sites = random.sample(WEBSITES, 3)
            sites_str = "\n".join(f"• {site}" for site in selected_sites)
            fallback_msg = (
                f"📚 HỌC TIẾNG ANH HÔM NAY - Ngày {vn_date}\n\n"
                "Hôm nay hệ thống không tìm thấy bài viết mới nào phù hợp.\n"
                "Bạn hãy thử truy cập vào 3 trang web đọc tiếng Anh thú vị dưới đây nhé:\n\n"
                f"{sites_str}\n\n"
                "Chúc bạn học tập vui vẻ! ✨"
            )
            delivery_success = notifier.send_zalo_message(fallback_msg, dry_run=args.dry_run)
            if not delivery_success:
                logger.error("Failed to send generic fallback message via Zalo Bot API.")
                sys.exit(1)
            sys.exit(0)
         
    # 5. Format the message for Zalo
    formatted_msg = notifier.format_message(curated_data)
    
    # 6. Deliver the message
    delivery_success = notifier.send_zalo_message(formatted_msg, dry_run=args.dry_run)
    if not delivery_success:
        logger.error("Failed to send message via Zalo Bot API.")
        sys.exit(1)
        
    # 7. Update sent_urls.txt cache (only if actual delivery succeeded and not dry-run)
    if not args.dry_run:
        selected_url = curated_data.get("url")
        if selected_url:
            dedup.add_sent_url(selected_url)
            logger.info("Pipeline finished successfully. State updated.")
        else:
            logger.warning("Selected article is missing a URL. State file was not updated.")
    else:
        logger.info("Dry run completed. Console output generated, state file unchanged.")

if __name__ == "__main__":
    main()
