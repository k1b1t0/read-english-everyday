import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from english_bot.topic_rotation import get_current_topic, get_this_week_topic

def test_get_current_topic():
    # Test Monday (0) -> Science & Space
    with patch('english_bot.topic_rotation.datetime') as mock_date:
        mock_date.now.return_value = datetime(2026, 7, 6, 12, 0, tzinfo=timezone(timedelta(hours=7)))
        assert get_current_topic()["slug"] == "science-space"
        assert get_this_week_topic() == "Science & Space"

    # Test Wednesday (2) -> Nature & Creative
    with patch('english_bot.topic_rotation.datetime') as mock_date:
        mock_date.now.return_value = datetime(2026, 7, 8, 12, 0, tzinfo=timezone(timedelta(hours=7)))
        assert get_current_topic()["slug"] == "nature-creative"
        assert get_this_week_topic() == "Nature & Creative"

    # Test Saturday (5) -> History, Culture & World
    with patch('english_bot.topic_rotation.datetime') as mock_date:
        mock_date.now.return_value = datetime(2026, 7, 11, 12, 0, tzinfo=timezone(timedelta(hours=7)))
        assert get_current_topic()["slug"] == "history-culture-world"
        assert get_this_week_topic() == "History, Culture & World"
