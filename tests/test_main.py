import pytest
from lambda_src.main import async_main, lambda_handler
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
@patch("lambda_src.main.get_secrets",
       return_value={"TELEGRAM_API_ID": "123", "TELEGRAM_API_HASH": "hash", "TELEGRAM_SESSION": "session"})
@patch("lambda_src.main.load_config")
@patch("lambda_src.main.initialize_telegram_client", new_callable=AsyncMock)
@patch("lambda_src.main.process_channel", new_callable=AsyncMock)
async def test_async_main_success(mock_process_channel, mock_init_client, mock_load_config, _mock_get_secrets):
    """ Test `async_main` when all dependencies work correctly."""
    mock_load_config.return_value = {
        "SYSTEM_CHANNEL_ID": -100123456789,
        "NUM_OF_MESSAGES_LIMIT": 300,
        "LLM_MODEL_NAME": "gpt-4",
        "LLM_TEMPERATURE": 0.7,
        "LLM_IMAGE_MODEL_NAME": "dall-e-3",
        "READER_TIMEZONE": "UTC",
        "channels": [{"SOURCE_CHANNEL_NAME": "Test Channel", "ENABLED": 1}]
    }

    mock_process_channel.return_value = None  # Simulating success

    result = await async_main({}, {})

    assert result["statusCode"] == 200
    assert "Successfully processed all channels." in result["body"]
    mock_init_client.assert_awaited_once()
    mock_process_channel.assert_awaited_once()


@pytest.mark.asyncio
@patch("lambda_src.main.get_secrets", side_effect=Exception("Secrets error"))
async def test_async_main_secrets_failure(_mock_get_secrets):
    """ Test `async_main` when `get_secrets` fails."""
    result = await async_main({}, {})

    assert result["statusCode"] == 500
    assert "Secrets error" in result["body"]


@pytest.mark.asyncio
@patch("lambda_src.main.get_secrets",
       return_value={"TELEGRAM_API_ID": "123", "TELEGRAM_API_HASH": "hash", "TELEGRAM_SESSION": "session"})
@patch("lambda_src.main.load_config", side_effect=Exception("Config file error"))
async def test_async_main_config_failure(_mock_load_config, _mock_get_secrets):
    """ Test `async_main` when `load_config` fails."""
    result = await async_main({}, {})

    assert result["statusCode"] == 500
    assert "Config file error" in result["body"]


@pytest.mark.asyncio
@patch("lambda_src.main.get_secrets",
       return_value={"TELEGRAM_API_ID": "123", "TELEGRAM_API_HASH": "hash", "TELEGRAM_SESSION": "session"})
@patch("lambda_src.main.load_config", return_value={"SYSTEM_CHANNEL_ID": -100123456789, "channels": [
    {"SOURCE_CHANNEL_NAME": "Test Channel", "ENABLED": 1}]})
@patch("lambda_src.main.initialize_telegram_client", new_callable=AsyncMock)
@patch("lambda_src.main.process_channel", side_effect=Exception("Process channel error"))
async def test_async_main_process_channel_failure(_mock_process_channel, _mock_init_client, _mock_load_config,
                                                  _mock_get_secrets):
    """ Test `async_main` when `process_channel` fails."""
    result = await async_main({}, {})

    assert result["statusCode"] == 500
    assert "Process channel error" in result["body"]


@patch("lambda_src.main.async_main", return_value={"statusCode": 200, "body": "Success"})
def test_lambda_handler(mock_async_main):
    """ Test `lambda_handler` calls `async_main` correctly."""
    result = lambda_handler({}, {})
    assert result["statusCode"] == 200
    assert "Success" in result["body"]
    mock_async_main.assert_called_once()


@pytest.mark.asyncio
@patch("lambda_src.main.get_secrets",
       return_value={"TELEGRAM_API_ID": "123", "TELEGRAM_API_HASH": "hash", "TELEGRAM_SESSION": "session"})
@patch("lambda_src.main.load_config",
       return_value={"SYSTEM_CHANNEL_ID": None, "channels": [{"SOURCE_CHANNEL_NAME": "Test Channel", "ENABLED": 1}]})
async def test_async_main_missing_system_channel_id(_mock_load_config, _mock_get_secrets):
    """✅ Test `async_main` when `SYSTEM_CHANNEL_ID` is missing or invalid."""
    result = await async_main({}, {})
    assert result["statusCode"] == 500
    assert "SYSTEM_CHANNEL_ID is missing or invalid" in result["body"]


@pytest.mark.asyncio
@patch("lambda_src.main.get_secrets",
       return_value={"TELEGRAM_API_ID": "123", "TELEGRAM_API_HASH": "hash", "TELEGRAM_SESSION": "session"})
@patch("lambda_src.main.load_config", return_value={"SYSTEM_CHANNEL_ID": -100123456789, "channels": [
    {"SOURCE_CHANNEL_NAME": "Test Channel", "ENABLED": 1}]})
@patch("lambda_src.main.initialize_telegram_client", new_callable=AsyncMock)
@patch("lambda_src.main.process_channel", new_callable=AsyncMock)
async def test_async_main_process_channel_unexpected_response(_mock_process_channel, _mock_init_client,
                                                              _mock_load_config, _mock_get_secrets):
    """ Test `async_main` when `process_channel()` returns an unexpected response."""
    _mock_process_channel.return_value = "Unexpected return value"

    result = await async_main({}, {})

    assert result["statusCode"] == 200
    assert "Successfully processed all channels" in result["body"]


@pytest.mark.asyncio
@patch("lambda_src.main.get_secrets",
       return_value={"TELEGRAM_API_ID": "123", "TELEGRAM_API_HASH": "hash", "TELEGRAM_SESSION": "session"})
@patch("lambda_src.main.load_config", return_value={"SYSTEM_CHANNEL_ID": -100123456789, "channels": [
    {"SOURCE_CHANNEL_NAME": "Test Channel", "ENABLED": 1}]})
@patch("lambda_src.main.initialize_telegram_client", new_callable=AsyncMock)
@patch("lambda_src.main.process_channel", side_effect=Exception("Process channel error"))
@patch("lambda_src.main.logging.getLogger")
async def test_async_main_sends_error_to_telegram(_mock_logger, _mock_process_channel, mock_init_client,
                                                  _mock_load_config, _mock_get_secrets):
    """ Test `async_main` attempts to send error message to Telegram system channel."""
    mock_client_instance = AsyncMock()
    mock_init_client.return_value = mock_client_instance

    result = await async_main({}, {})

    assert result["statusCode"] == 500
    assert "Process channel error" in result["body"]
    mock_client_instance.send_message.assert_awaited_once_with(-100123456789,
                                                               "Critical error in Lambda execution: Process channel "
                                                               "error")


@pytest.mark.asyncio
@patch("lambda_src.main.get_secrets", return_value={"TELEGRAM_API_ID": "123", "TELEGRAM_API_HASH": "hash",
                                                    "TELEGRAM_SESSION": "session"})
@patch("lambda_src.main.load_config", return_value={"SYSTEM_CHANNEL_ID": -100123456789, "channels": []})
@patch("lambda_src.main.initialize_telegram_client", new_callable=AsyncMock)
async def test_async_main_no_channels(_mock_init_client, _mock_load_config, _mock_get_secrets):
    """ Test `async_main` when `channels` list is empty in config."""
    result = await async_main({}, {})

    assert result["statusCode"] == 200
    assert "Successfully processed all channels" in result["body"]

    _mock_init_client.assert_awaited_once()
