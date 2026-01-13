# MyFeed - AI-Powered Newsletter System

An intelligent newsletter system that uses LangGraph agents to scrape the web for relevant articles based on your interests and sends you a personalized daily newsletter at 8am.

## Features

- 🤖 AI-powered content curation using LangGraph
- 📧 Automated email delivery with HTML formatting
- ⏰ Flexible scheduling (daily at 8am by default)
- 🎯 Customizable topics of interest
- 📰 Multi-source news aggregation from RSS feeds
- 🔧 Easy configuration via environment variables

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**
   Copy `.env.example` to `.env` and fill in your details:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `EMAIL_ADDRESS`: Your Gmail address
   - `EMAIL_PASSWORD`: Your Gmail app password (not your regular password)
   - `TO_EMAIL`: Where to send the newsletter (can be the same as EMAIL_ADDRESS)
   - `TOPICS`: Comma-separated list of interests (e.g., "AI,Python,Technology,Startups")

3. **Gmail App Password Setup**
   - Enable 2-factor authentication on your Gmail account
   - Generate an app password: Google Account → Security → App passwords
   - Use this app password in the `EMAIL_PASSWORD` field

## Usage

- **Test Configuration**: `python main.py test`
- **Generate One Newsletter**: `python main.py run-once`
- **Start Scheduler**: `python main.py start`
- **View Configuration**: `python main.py config`

## How It Works

1. **Scraping**: The LangGraph agent fetches articles from multiple tech news sources
2. **Filtering**: AI analyzes each article's relevance to your specified topics
3. **Curation**: Top articles are selected and summarized
4. **Delivery**: A formatted newsletter is sent to your email

## GitHub Actions Deployment

The project includes a GitHub workflow for automated daily newsletters:

1. **Set up repository secrets** (Settings → Secrets and variables → Actions):
   ```
   OPENAI_API_KEY=your_openai_api_key
   EMAIL_ADDRESS=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   TO_EMAIL=your_email@gmail.com
   TOPICS=AI,Python,Technology,Startups
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   NEWSLETTER_TIME=08:00
   TIMEZONE=UTC
   ```

2. **Push to GitHub** - The workflow runs automatically at 8 AM UTC daily

3. **Manual trigger** - Go to Actions tab → "Daily Newsletter" → "Run workflow"

4. **Timezone adjustment** - Modify the cron schedule in `.github/workflows/newsletter.yml`:
   - `0 8 * * *` = 8:00 AM UTC
   - `0 13 * * *` = 8:00 AM EST (UTC-5)
   - `0 15 * * *` = 8:00 AM PST (UTC-8)

## Customization

- **Topics**: Edit the `TOPICS` field in `.env` or GitHub secrets
- **Schedule**: Change cron schedule in workflow file and `NEWSLETTER_TIME`
- **Sources**: Modify the RSS feed list in `src/agent.py`
