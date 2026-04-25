# MyFeed: My AI-Powered Newsletter Generator

An automated newsletter system that uses an agent to scrape the web for relevant articles based on my interests and sends me a personalized daily newsletter.

## Features

- 🤖 AI-powered content curation using LangGraph + Mistral AI
- 📧 Automated email delivery with HTML formatting
- ⏰ Flexible scheduling (daily at 8am CST by default)
- 🎯 Customizable topics of interest
- 📰 Multi-source news aggregation from RSS feeds
- 🎓 Academic paper discovery via OpenAlex API
- 🌟 Positive news section alongside tech content

## Setup

1. **Install Dependencies**
   ```bash
   uv sync
   ```

2. **Required Credentials**
   - `MISTRAL_API_KEY`: Your Mistral AI API key
   - `EMAIL_ADDRESS`: Your Gmail address
   - `EMAIL_PASSWORD`: Your Gmail app password (not your regular password)
   - `TO_EMAIL`: Where to send the newsletter (can be the same as EMAIL_ADDRESS)
   - `TOPICS`: Comma-separated list of interests (e.g., "AI,Python,Technology,Startups")

3. **Gmail App Password Setup**
   - Enable 2-factor authentication on your Gmail account
   - Generate an app password: Google Account → Security → App passwords
   - Use this app password in the `EMAIL_PASSWORD` field

## Usage

All commands require the following flags:

```
--mistral-api-key     Your Mistral API key
--email-address       Gmail address for sending
--email-password      Gmail app password
--to-email            Recipient email address
--topics              Comma-separated list of interests (optional)
```

- **Test Configuration**:
  ```bash
  uv run python main.py test --mistral-api-key <key> --email-address <addr> --email-password <pwd> --to-email <addr>
  ```
- **Generate One Newsletter**:
  ```bash
  uv run python main.py run-once --mistral-api-key <key> --email-address <addr> --email-password <pwd> --to-email <addr>
  ```
- **View Configuration**:
  ```bash
  uv run python main.py config --mistral-api-key <key> --email-address <addr> --email-password <pwd> --to-email <addr>
  ```

## How It Works

1. **Scraping**: The LangGraph agent fetches articles from multiple tech news sources, positive news RSS feeds, and academic papers via the OpenAlex API
2. **Filtering**: Mistral AI analyzes each article's relevance to your specified topics (scores ≥6/10 are kept)
3. **Curation**: Top articles are selected and summarized
4. **Delivery**: A formatted newsletter is sent to your email with separate sections for positive news, tech news, and papers

## GitHub Actions Deployment

The project includes a GitHub workflow for automated daily newsletters:

1. **Set up repository secrets** (Settings → Secrets and variables → Actions):
   ```
   MISTRAL_API_KEY=your_mistral_api_key
   EMAIL_ADDRESS=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   TO_EMAIL=your_email@gmail.com
   TOPICS=AI,Python,Technology,Startups
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```

2. **Push to GitHub** - The workflow runs automatically at 14:00 UTC (8:00 AM CST) daily

3. **Manual trigger** - Go to Actions tab → "Daily Newsletter" → "Run workflow"

4. **Timezone adjustment** - Modify the cron schedule in `.github/workflows/newsletter.yml`:
   - `0 14 * * *` = 8:00 AM CST (UTC-6) / 9:00 AM CDT (UTC-5)
   - `0 13 * * *` = 8:00 AM EST (UTC-5)
   - `0 16 * * *` = 8:00 AM PST (UTC-8)

## Customization

- **Topics**: Pass `--topics` flag when running, or update the `TOPICS` secret in GitHub Actions
- **Schedule**: Change the cron schedule in `.github/workflows/newsletter.yml`
- **Sources**: Modify the RSS feed list in `myfeed/agent.py`
