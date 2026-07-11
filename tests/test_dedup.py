import os
import pytest
from english_bot.dedup import normalize_url, load_sent_urls, add_sent_url

def test_normalize_url():
    # News in levels URL cleaning rules
    assert normalize_url("https://www.newsinlevels.com/products/test-article-level-1/") == "https://www.newsinlevels.com/products/test-article"
    assert normalize_url("https://www.newsinlevels.com/products/another-test-level-3") == "https://www.newsinlevels.com/products/another-test"
    # General URL trimming
    assert normalize_url("https://example.com/some-page/") == "https://example.com/some-page"
    assert normalize_url("") == ""
    assert normalize_url(None) == ""

def test_load_and_add_sent_urls(tmp_path):
    temp_file = os.path.join(tmp_path, "test_sent_urls.txt")
    
    # Initially empty
    sent = load_sent_urls(temp_file)
    assert len(sent) == 0
    
    # Add a URL
    add_sent_url("https://example.com/test-level-2/", filepath=temp_file)
    sent2 = load_sent_urls(temp_file)
    # It should be normalized when added
    assert "https://example.com/test" in sent2
    assert len(sent2) == 1
    
    # Adding again doesn't duplicate
    add_sent_url("https://example.com/test/", filepath=temp_file)
    sent3 = load_sent_urls(temp_file)
    assert len(sent3) == 1
