import requests
from datetime import datetime, timedelta, timezone
from summarizer import summarize_messages, generate_image


def process_channel(
    client,
    channel_config,
    llm_model_name,
    llm_temperature,
    image_model_name,
    reader_timezone,
    num_of_messages_limit,
    system_channel_id
):
    """Processes a single Telegram channel."""
    try:
        # Skip the channel if not enabled
        if channel_config.get("ENABLED", 1) == 0:
            client.send_message(
                system_channel_id,
                f"Skipping channel {channel_config.get('SOURCE_CHANNEL_NAME', 'Unknown')} as it is disabled."
            )
            return

        source_channel_id = channel_config["SOURCE_CHANNEL_ID"]
        summary_channel_id = channel_config["SUMMARY_CHANNEL_ID"]
        generate_image_flag = channel_config.get("GENERATE_IMAGE", 0)
        summary_period_hours = channel_config.get("SUMMARY_PERIOD_HOURS", 24)

        # Define the time window
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=summary_period_hours)
        all_messages = []

        # Fetch messages from the source channel
        channel = client.get_entity(source_channel_id)
        last_date = None
        total_messages_fetched = 0

        while True:
            batch = client.get_messages(channel, limit=100, offset_date=last_date)
            if not batch:
                break

            for msg in batch:
                if msg.date >= start_date:
                    all_messages.append(msg)
                else:
                    break

                total_messages_fetched += 1
                if total_messages_fetched >= num_of_messages_limit:
                    break

            last_date = batch[-1].date if batch else None
            if last_date and last_date < start_date:
                break
            if total_messages_fetched >= num_of_messages_limit:
                break

        # Ensure messages are in chronological order
        all_messages.reverse()

        # If no messages, post only the time period and message count
        if not all_messages:
            time_period = f"**Time period:** {start_date.strftime('%Y-%m-%d %H:%M:%S')} to {end_date.strftime('%Y-%m-%d %H:%M:%S')}"
            message_count_text = "**Number of messages:** 0"
            client.send_message(summary_channel_id, f"{time_period}\n{message_count_text}")
            client.send_message(
                system_channel_id,
                f"Channel {channel_config.get('SOURCE_CHANNEL_NAME', 'Unknown')} has no new messages."
            )
            return

        # Summarize messages
        summary_text = summarize_messages(
            all_messages,
            start_date,
            end_date,
            llm_model_name,
            llm_temperature,
            reader_timezone
        )

        # Post the summary text
        client.send_message(summary_channel_id, summary_text)

        # If GENERATE_IMAGE == 1, generate and post the image
        if generate_image_flag == 1:
            image_url = generate_image(summary_text, image_model_name)
            image_path = "/tmp/summary_image.png"

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
        error_message = f"Error processing channel {channel_config.get('SOURCE_CHANNEL_NAME', 'Unknown')}: {e}"
        client.send_message(system_channel_id, error_message)
