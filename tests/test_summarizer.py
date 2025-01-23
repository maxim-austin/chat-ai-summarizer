import pytest
import datetime
from unittest.mock import patch, AsyncMock
from lambda_src.summarizer import summarize_messages, generate_image
from unittest.mock import MagicMock


@pytest.fixture
def fake_messages():
    """ Fixture to create fake Telegram messages."""

    def create_fake_message(text):
        msg = MagicMock()
        msg.text = text
        msg.sender = MagicMock()
        msg.sender.first_name = "Alice"
        msg.sender.last_name = "Smith"
        return msg

    return [
        create_fake_message("Hello, how are you?"),
        create_fake_message("I'm good! How about you?"),
        create_fake_message("Let's discuss our project.")
    ]


def test_summarize_messages_no_messages():
    """ Test when no messages are provided."""
    summary = summarize_messages(
        messages=[],
        start_date=datetime.datetime.now(datetime.UTC),
        end_date=datetime.datetime.now(datetime.UTC),
        llm_model_name="gpt-4",
        llm_temperature=0.7,
        reader_timezone="UTC",
        openai_api_key="fake_key"
    )
    assert summary == "**[No meaningful messages were found to summarize]**"


@patch("lambda_src.summarizer.ChatOpenAI")
def test_summarize_messages(mock_chat_openai, fake_messages):
    """ Test summarization process with valid messages."""
    mock_chat_instance = mock_chat_openai.return_value
    mock_chat_instance.invoke.return_value.content = "Summary of the discussion."

    summary = summarize_messages(
        messages=fake_messages,
        start_date=datetime.datetime.now(datetime.UTC),
        end_date=datetime.datetime.now(datetime.UTC),
        llm_model_name="gpt-4",
        llm_temperature=0.7,
        reader_timezone="UTC",
        openai_api_key="fake_key"
    )

    assert "Summary of the discussion." in summary
    assert "**Number of messages:** 3" in summary


@patch("lambda_src.summarizer.ChatOpenAI")
def test_summarize_messages_api_failure(mock_chat_openai, fake_messages):
    """ Test API failure handling in summarization."""
    mock_chat_instance = mock_chat_openai.return_value
    mock_chat_instance.invoke.side_effect = Exception("API error")

    summary = summarize_messages(
        messages=fake_messages,
        start_date=datetime.datetime.now(datetime.UTC),
        end_date=datetime.datetime.now(datetime.UTC),
        llm_model_name="gpt-4",
        llm_temperature=0.7,
        reader_timezone="UTC",
        openai_api_key="fake_key"
    )

    assert "**[Error occurred during summarization:" in summary


@pytest.mark.asyncio
@patch("lambda_src.summarizer.aiohttp.ClientSession.post")
async def test_generate_image_success(mock_post):
    """ Test successful image generation."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"data": [{"url": "https://fakeimage.com/image.png"}]}
    mock_post.return_value.__aenter__.return_value = mock_response

    image_url = await generate_image(
        summary_text="Summary content",
        image_model_name="dall-e-3",
        openai_api_key="fake_key"
    )

    assert image_url == "https://fakeimage.com/image.png"


@pytest.mark.asyncio
@patch("lambda_src.summarizer.aiohttp.ClientSession.post")
async def test_generate_image_failure(mock_post):
    """ Test OpenAI API failure handling."""
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text.return_value = "Internal Server Error"
    mock_post.return_value.__aenter__.return_value = mock_response

    image_url = await generate_image(
        summary_text="Summary content",
        image_model_name="dall-e-3",
        openai_api_key="fake_key"
    )

    assert "**[Error occurred while generating image]**" in image_url


@pytest.mark.asyncio
@patch("lambda_src.summarizer.aiohttp.ClientSession.post")
async def test_generate_image_network_error(mock_post):
    """ Test handling of network failures."""
    mock_post.side_effect = Exception("Network error")

    image_url = await generate_image(
        summary_text="Summary content",
        image_model_name="dall-e-3",
        openai_api_key="fake_key"
    )

    assert "**[Error occurred while generating image]**" in image_url
