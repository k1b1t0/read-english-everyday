import pytest
from unittest.mock import patch, MagicMock
from english_bot.feeds import fetch_articles, clean_summary

def test_clean_summary():
    assert clean_summary("<p>Hello <b>World</b></p>") == "Hello World"
    assert clean_summary("Hello   \n   World") == "Hello World"
    assert clean_summary("A" * 500, max_chars=10) == "AAAAAAAAAA..."
    assert clean_summary("") == ""
    assert clean_summary(None) == ""

@patch('requests.get')
def test_fetch_articles(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
 <title>Test RSS Feed</title>
 <link>http://example.com</link>
 <description>Test Description</description>
 <item>
  <title>Test Article Title</title>
  <link>https://www.newsinlevels.com/products/test-article-level-1/</link>
  <description>Hello world summary.</description>
 </item>
</channel>
</rss>"""
    mock_get.return_value = mock_response

    articles = fetch_articles("Science & Space", max_items=5)
    assert len(articles) == 1
    # Check that the URL was normalized during parsing
    assert articles[0]["url"] == "https://www.newsinlevels.com/products/test-article"
    assert articles[0]["title"] == "Test Article Title"
    assert articles[0]["summary"] == "Hello world summary."
