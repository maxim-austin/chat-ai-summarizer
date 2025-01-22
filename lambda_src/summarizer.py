import logging
import requests
from pytz import timezone
from langchain.prompts.chat import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain_openai import ChatOpenAI
from typing import List
from datetime import datetime
from telethon.tl.custom.message import Message

# Set up logging
logger = logging.getLogger(__name__)


def summarize_messages(
        messages: List[Message],
        start_date: datetime,
        end_date: datetime,
        llm_model_name: str,
        llm_temperature: float,
        reader_timezone: str,
        openai_api_key: str
) -> str:
    """Summarizes a list of messages and returns a text summary."""
    try:
        if not messages:  # Handle case when there are no messages
            logger.info("No messages to summarize.")
            return "**[No meaningful messages were found to summarize]**"

        user_tz = timezone(reader_timezone)
        start_date_tz = start_date.astimezone(user_tz)
        end_date_tz = end_date.astimezone(user_tz)

        # Prepare conversation text
        conversation_text = []
        for msg in messages:
            sender = msg.sender
            sender_name = (
                f"{sender.first_name or ''} {sender.last_name or ''}".strip()
                if sender else "Unknown"
            )
            message_text = msg.text or "<no text>"
            conversation_text.append(f"{sender_name}: {message_text}")

        conversation_str = "\n".join(conversation_text)

        # Define the prompt
        system_template = """Вы являетесь помощником, который резюмирует активность канала Telegram. 
        Сосредоточьтесь на том, какие темы обсуждались и кем."""
        human_template = f"""Резюмируйте следующий разговор на русском языке.
        Включите, какие темы обсуждались и кем (имена участников).
        Период: {start_date_tz.strftime('%Y-%m-%d %H:%M:%S')} - {end_date_tz.strftime('%Y-%m-%d %H:%M:%S')}
        Разговор:
        {conversation_str}"""

        # Create LangChain prompts
        system_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])

        # Summarize using OpenAI
        chat_llm = ChatOpenAI(
            model_name=llm_model_name,
            temperature=llm_temperature,
            openai_api_key=openai_api_key
        )
        prompt_messages = chat_prompt.format_prompt(conversation=conversation_str).to_messages()
        response = chat_llm.invoke(prompt_messages)

        # Ensure response is a valid string
        summary_text = response.content if response and response.content else "**[No meaningful summary generated]**"

        # Add metadata to the summary
        message_count = len(messages)
        time_period = f"**Time period:** {start_date_tz.strftime('%Y-%m-%d %H:%M:%S')} to {end_date_tz.strftime('%Y-%m-%d %H:%M:%S')}"
        message_count_text = f"**Number of messages:** {message_count}"
        return f"{time_period}\n{message_count_text}\n\n{summary_text}"

    except Exception as e:
        error_message = f"Error summarizing messages: {e}"
        logger.error(error_message)
        return f"**[Error occurred during summarization: {e}]**"


def generate_image(summary_text: str, image_model_name: str, openai_api_key: str) -> str:
    """Generates an image using OpenAI's API based on summary text."""
    try:
        # Define the prompt
        image_prompt = (
            f"Extract and identify up to 3 key topics from the summary provided below, "
            f"then create a cozy painterly-style illustration with soft textures and warm, inviting tones. "
            f"The image should be divided into separate segments, each representing one of the identified topics. "
            f"Focus solely on illustrating the discussed items (e.g., cars, food, or objects) rather than including people. "
            f"Do not include text, captions, or labels in the illustration. "
            f"Use subtle, natural lighting and rich, warm colors to evoke a sense of comfort and harmony, "
            f"with no overly modern or abstract elements.\n\n"
            f"<summary>{summary_text}</summary>"
        )

        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {openai_api_key}", "Content-Type": "application/json"},
            json={"prompt": image_prompt, "n": 1, "size": "1024x1024", "model": image_model_name}
        )
        response.raise_for_status()
        return response.json()["data"][0]["url"]
    except Exception as e:
        error_message = f"Error generating image: {e}"
        logger.error(error_message)
        return "**[Error occurred while generating image]**"
