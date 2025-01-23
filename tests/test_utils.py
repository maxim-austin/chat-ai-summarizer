import pytest
import os
from unittest.mock import patch, AsyncMock
from moto import mock_aws
import boto3
from lambda_src.utils import get_secrets, load_config, initialize_telegram_client
from telethon.sessions import StringSession

# Define test config file path
TEST_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test_config.json")


def test_load_config():
    """ Test that JSON configuration is loaded correctly from the test file."""
    config = load_config(TEST_CONFIG_PATH)

    assert isinstance(config, dict), "Config should be a dictionary"
    assert "LLM_MODEL_NAME" in config, "LLM_MODEL_NAME missing from config"
    assert config["LLM_MODEL_NAME"] == "gpt-4o-mini", "Unexpected LLM_MODEL_NAME value"
    assert config["NUM_OF_MESSAGES_LIMIT"] == 300, "NUM_OF_MESSAGES_LIMIT should be 300"


def test_get_secrets_local(monkeypatch):
    """ Test retrieving secrets from local .env file."""
    monkeypatch.setenv("TELEGRAM_API_ID", "12345")
    monkeypatch.setenv("TELEGRAM_API_HASH", "fake_hash")
    monkeypatch.setenv("TELEGRAM_SESSION", "fake_session")
    monkeypatch.setenv("OPENAI_API_KEY", "fake_openai_key")

    secrets = get_secrets()

    assert secrets["TELEGRAM_API_ID"] == "12345", "TELEGRAM_API_ID should be 12345"
    assert secrets["TELEGRAM_API_HASH"] == "fake_hash", "TELEGRAM_API_HASH should match"
    assert secrets["TELEGRAM_SESSION"] == "fake_session", "TELEGRAM_SESSION should match"
    assert secrets["OPENAI_API_KEY"] == "fake_openai_key", "OPENAI_API_KEY should match"


@mock_aws
def test_get_secrets_aws_lambda(monkeypatch):
    """ Test retrieving secrets from AWS SSM Parameter Store."""
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "test_lambda")  # Simulate Lambda environment

    ssm = boto3.client("ssm", region_name="us-west-2")

    # Mock AWS SSM secrets
    ssm.put_parameter(Name="TELEGRAM_API_ID", Value="12345", Type="SecureString")
    ssm.put_parameter(Name="TELEGRAM_API_HASH", Value="fake_hash", Type="SecureString")
    ssm.put_parameter(Name="TELEGRAM_SESSION", Value="fake_session", Type="SecureString")
    ssm.put_parameter(Name="OPENAI_API_KEY", Value="fake_openai_key", Type="SecureString")

    secrets = get_secrets()

    assert secrets["TELEGRAM_API_ID"] == "12345", "TELEGRAM_API_ID should be 12345"
    assert secrets["TELEGRAM_API_HASH"] == "fake_hash", "TELEGRAM_API_HASH should match"
    assert secrets["TELEGRAM_SESSION"] == "fake_session", "TELEGRAM_SESSION should match"
    assert secrets["OPENAI_API_KEY"] == "fake_openai_key", "OPENAI_API_KEY should match"


def generate_fake_telegram_session():
    """Generate a valid fake Telegram session string."""
    return StringSession().save()


@pytest.mark.asyncio
@patch("lambda_src.utils.TelegramClient")
async def test_initialize_telegram_client(mock_telegram_client):
    """ Test that Telegram client initializes successfully with a valid session string."""
    mock_client_instance = AsyncMock()
    mock_telegram_client.return_value = mock_client_instance
    mock_client_instance.connect.return_value = None
    mock_client_instance.is_user_authorized.return_value = True  # Simulate authorized session

    fake_session = generate_fake_telegram_session()  # Generate valid session

    secrets = {
        "TELEGRAM_API_ID": "12345",
        "TELEGRAM_API_HASH": "fake_hash",
        "TELEGRAM_SESSION": fake_session,  # Use generated session string
    }

    client = await initialize_telegram_client(secrets)

    assert client == mock_client_instance, "Telegram client instance mismatch"
    mock_client_instance.connect.assert_awaited_once(), "Client should attempt to connect"
    mock_client_instance.is_user_authorized.assert_awaited_once(), "Authorization check should happen"
