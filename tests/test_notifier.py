import pytest
from english_bot.notifier import format_message

def test_format_message_no_story():
    data = {
        "title": "Parthenon Curation",
        "url": "https://www.newsinlevels.com/products/parthenon",
        "topic": "History, Culture & World",
        "vocab_words": ["restoration", "temple"],
        "phrases": ["famous monument", "open and clean"],
    }
    messages = format_message(data)
    assert len(messages) == 1
    assert "📚 BÀI ĐỌC TIẾNG ANH HÔM NAY" in messages[0]
    assert "Parthenon Curation" in messages[0]
    assert "https://www.newsinlevels.com/products/parthenon" in messages[0]
    assert "• restoration  • temple" in messages[0]
    assert "1. famous monument" in messages[0]

def test_format_message_with_story():
    data = {
        "title": "Parthenon Curation",
        "url": "https://www.newsinlevels.com/products/parthenon",
        "topic": "History, Culture & World",
        "vocab_words": ["restoration", "temple"],
        "phrases": ["famous monument", "open and clean"],
        "story_passage": "This is a daily conversation practice story.",
    }
    messages = format_message(data)
    assert len(messages) == 2
    assert "ĐOẠN VÍ DỤ\n\nThis is a daily conversation practice story." in messages[1]
