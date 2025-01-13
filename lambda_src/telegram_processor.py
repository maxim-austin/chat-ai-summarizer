import os
import requests
from datetime import datetime, timedelta, timezone
from summarizer import summarize_messages, generate_image

def process_channel(
    client,
    channel_config,
    llm_model_name,
    llm_temperature,
    image_model_name,
    reader_timezone
):
    """Processes a single Telegram channel."""
    try:
        source_channel_id = channel_config["SOURCE_CHANNEL_ID"]
        summary_channel_id = channel_config["SUMMARY_CHANNEL_ID"]
        generate_image_flag = channel_config.get("GENERATE_IMAGE", 0)

        # Define the time window
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=1)
        all_messages = []

        # Fetch messages from the source channel
        channel = client.get_entity(source_channel_id)
        last_date = None

        while True:
            batch = client.get_messages(channel, limit=100, offset_date=last_date)
            if not batch:
                break

            for msg in batch:
                if msg.date >= start_date:
                    all_messages.append(msg)
                else:
                    break

            last_date = batch[-1].date if batch else None
            if last_date and last_date < start_date:
                break

        # Ensure messages are in chronological order
        all_messages.reverse()

        # Summarize messages (pass reader_timezone to summarizer)
        summary_text = summarize_messages(
            all_messages,
            start_date,
            end_date,
            llm_model_name,
            llm_temperature,
            reader_timezone
        )

        # 1) Post the summary text
        client.send_message(summary_channel_id, summary_text)

        # 2) If GENERATE_IMAGE == 1, generate and post the image
        if generate_image_flag == 1:
            image_url = generate_image(summary_text, image_model_name)
            image_path = "summary_image.png"

            # Download the image locally
            image_data = requests.get(image_url)
            if image_data.status_code == 200:
                with open(image_path, "wb") as f:
                    f.write(image_data.content)
            else:
                raise Exception(
                    f"Failed to download image: {image_data.status_code} - {image_data.text}"
                )

            # Post the image with a short caption
            client.send_file(summary_channel_id, image_path, caption="Illustration for the summary above")

    except Exception as e:
        print(f"Error processing channel {channel_config.get('SOURCE_CHANNEL_NAME', 'Unknown')}: {e}")
