import os
import pytest
from unittest.mock import patch, MagicMock
from english_bot.curator import curate_article

def test_curate_article_mock():
    candidates = [{"title": "Test Title", "url": "https://example.com", "summary": "Test Summary"}]
    data = curate_article(candidates, "Science & Space", mock=True)
    assert data["title"] == "Test Title"
    assert data["url"] == "https://example.com"
    assert len(data["vocab_words"]) == 5
    assert len(data["phrases"]) == 10

@patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
@patch('english_bot.curator.genai.Client')
def test_curate_article_llm(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    # Mock return JSON matching our CuratedArticle Pydantic schema
    mock_response.text = '{"title": "Test Title", "url": "https://example.com", "topic": "Science & Space", "vocab_words": ["a","b","c","d","e"], "phrases": ["p1","p2","p3","p4","p5","p6","p7","p8","p9","p10"], "story_passage": "Hello story"}'
    mock_client.models.generate_content.return_value = mock_response

    candidates = [{"title": "Test Title", "url": "https://example.com", "summary": "Test Summary"}]
    data = curate_article(candidates, "Science & Space")
    
    assert data is not None
    assert data["title"] == "Test Title"
    assert data["url"] == "https://example.com"
    assert data["story_passage"] == "Hello story"
