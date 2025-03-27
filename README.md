# Telegram Advanced Message Forwarder

A sophisticated Telegram message forwarding bot with advanced channel management capabilities and a user-friendly web interface.

## Features

- Forward messages between Telegram channels and groups
- Web dashboard for easy configuration and monitoring
- Resume interrupted forwarding
- Rate-limited forwarding (1 message every 3 seconds)
- Support for restricted channels/groups
- Copy-to-clipboard functionality for channel links

## Requirements

- Python 3.11+
- PostgreSQL database
- Telegram API credentials (API ID and API Hash)
- Telegram Bot Token

## Environment Variables

The following environment variables need to be set:

```
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=your_postgresql_database_url
PGHOST=your_database_host
PGPORT=your_database_port
PGUSER=your_database_user
PGPASSWORD=your_database_password
PGDATABASE=your_database_name
```

## Deployment to Koyeb

1. Fork this repository to your GitHub account
2. Create a new application on Koyeb
3. Connect to your GitHub repository
4. Set all required environment variables
5. Deploy the application

## Local Development

1. Clone this repository
2. Install dependencies: `pip install -r requirements_koyeb.txt`
3. Set up required environment variables
4. Run the application: `gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app`

## Usage

1. Access the web dashboard
2. Login with your Telegram API credentials
3. Add source and destination channels
4. Configure forwarding settings
5. Start forwarding messages

## Health Endpoint

The application provides a `/health` endpoint that returns a JSON response with the status of the service. This can be used for uptime monitoring with services like Hetrix Tools.