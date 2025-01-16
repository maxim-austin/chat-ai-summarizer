# GenAI Telegram Chat Summarizer

## 1. Overview
This GenAI application summarizes the contents of specified Telegram channels using an OpenAI LLM and optionally generates an accompanying illustration. The high-level flow is:

1. **Fetch Messages**: Reads recent messages from a source Telegram channel.  
2. **Summarize**: Sends them to an LLM (e.g., GPT-4) for text summarization.  
3. **Generate Image** (Optional): Uses OpenAI’s image-generation endpoint to create an illustration based on the summary.  
4. **Publish**: Posts the summary (and image, if enabled) to a designated Telegram channel.

All system logs (including errors) are sent to a separate **System** channel for easy troubleshooting.

---

## 2. Prerequisites

To get started, you will need to have your **Telegram API credentials**, **OpenAI API key**, and all configuration parameters properly defined.

1. **Telegram API Secrets**  
   - **API_ID**: Your Telegram API ID  
   - **API_HASH**: Your Telegram API Hash  
   - **SESSION**: A valid Telegram session string  

2. **OpenAI API Key**  
   - **OPENAI_API_KEY**: Required to call text summarization (LangChain/OpenAI) and image-generation (DALL·E) endpoints.  

3. **Telegram Channels**  
   - **SOURCE_CHANNEL_ID**: The Telegram channel ID(s) you want to summarize.  
   - **SUMMARY_CHANNEL_ID**: The channel where you want to publish the summary text (and optionally images).  
   - **SYSTEM_CHANNEL_ID**: A dedicated channel for logs and error messages.  

4. **Other Config Parameters**  
   - **LLM_MODEL_NAME**: Which LLM to use (e.g., `gpt-4`).  
   - **LLM_TEMPERATURE**: LLM temperature setting.  
   - **SUMMARY_PERIOD_HOURS**: How many hours of chat history to summarize.  
   - **NUM_OF_MESSAGES_LIMIT**: Maximum number of recent messages to retrieve.  
   - **GENERATE_IMAGE**: Whether to generate an illustration (1 = yes, 0 = no).  
   - **ENABLED**: Whether the channel is active in the summarization process (1 = yes, 0 = no).

**Secrets Storage**:  
- For **cloud deployment**, Telegram and OpenAI secrets are expected to be stored in **AWS Systems Manager Parameter Store**.  
- For **local execution**, secrets should be stored in a `.env` file.

---

## 3. AWS Deployment & Terraform

This application is designed primarily for **AWS deployment**. The deployment process leverages **Terraform** to define and provision the required cloud infrastructure, including:

- **AWS Lambda**: Executes the summarization and image generation.  
- **Amazon S3**: Stores the Lambda deployment package and the Terraform state file.  
- **CloudWatch EventBridge**: Triggers the Lambda function on a defined schedule (e.g., daily).  
- **IAM Roles**: Grants the Lambda function necessary permissions (e.g., to access AWS Systems Manager Parameter Store).

### **Deployment Process**
The project uses a **GitHub Actions workflow** to trigger the Terraform deployment automatically upon merging the code to the `main` branch.

- **AWS Credentials**: Ensure the following secrets are stored in the GitHub repository to allow Terraform and GitHub Actions to deploy resources:
  - **AWS_ACCOUNT_ID**
  - **AWS_ACCESS_KEY_ID**
  - **AWS_SECRET_ACCESS_KEY**

---

## 4. Python Functions & Dependencies

### **main.py**
- **`lambda_handler(event, context)`**: Entry point for AWS Lambda.  
- Loads secrets (Telegram, OpenAI) from AWS SSM Parameter Store or from `.env` (local).  
- Reads config from `config.json`, initializes the Telegram client, and calls `process_channel(...)` for each channel.

### **telegram_processor.py**
- **`process_channel(...)`**: Core function that:
  1. Validates if the channel is enabled.  
  2. Fetches messages within a specified period and up to a set limit.  
  3. Calls **`summarize_messages(...)`** to generate text.  
  4. Optionally calls **`generate_image(...)`** and posts the results to a target channel.  
  5. Logs errors and outputs to the system channel.

### **summarizer.py**
- **`summarize_messages(...)`**: Uses LangChain/OpenAI to produce a text summary from given messages.  
- **`generate_image(...)`**: Creates a prompt from the text summary and calls OpenAI’s image-generation endpoint to produce an illustration.

### **Dependencies**
- **Telethon**: For Telegram client interactions.  
- **LangChain**: Abstraction layer for ChatGPT/OpenAI LLM usage.  
- **requests**: For image-generation API calls (and image downloading).  
- **boto3** (in Lambda): For AWS SSM Parameter Store if running in AWS.  
- **python-dotenv**: For local `.env` usage.

---

## How to Get Started Locally
1. Clone the repo and install dependencies (e.g., `pip install -r requirements.txt`).  
2. Create a `.env` file with your Telegram and OpenAI credentials.  
3. Update or create `config.json` with your channel IDs and other parameters.  
4. Run `python main.py` to test.