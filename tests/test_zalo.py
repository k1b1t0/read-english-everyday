import os
import pytest
from unittest.mock import patch, MagicMock
from shared.zalo import send_zalo_message

@patch.dict(os.environ, {"ZALO_BOT_TOKEN": "fake_token", "ZALO_CHAT_ID": "id1,id2"})
@patch('requests.post')
def test_send_zalo_message(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True}
    mock_post.return_value = mock_response

    success = send_zalo_message("Hello Zalo")
    assert success is True
    
    # Verify that requests.post was called for each Chat ID in the list
    assert mock_post.call_count == 2
