import pytest
from unittest.mock import AsyncMock
from lambda_src.telegram_processor import process_channel
from telethon import TelegramClient


@pytest.mark.asyncio
async def test_process_channel_no_messages(monkeypatch):
    """ Test process_channel when no messages are found"""

    mock_client = AsyncMock(TelegramClient)
    mock_client.get_entity.return_value = "fake_channel"
    mock_client.get_messages.return_value = []

    mock_secrets = {
        "OPENAI_API_KEY": "fake_openai_key"
    }
    mock_config = {
        "SOURCE_CHANNEL_ID": -100123456789,
        "SUMMARY_CHANNEL_ID": -100987654321,
        "GENERATE_IMAGE": 0,
        "SUMMARY_PERIOD_HOURS": 24
    }

    await process_channel(mock_client, mock_config, mock_secrets, 100, "gpt-4", 0.7, "US/Central", "dall-e-3",
                          -10054321)

    mock_client.send_message.assert_called_with(-10054321, "No new messages found for channel Unknown")
