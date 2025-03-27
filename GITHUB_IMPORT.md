# GitHub Import and Deployment Guide

This guide will walk you through the process of importing this Telegram Advanced Message Forwarder from Replit to GitHub and deploying it on various platforms.

## Import to GitHub

### Method 1: Using GitHub's Import Repository Feature (Easiest)

1. **Login to GitHub**:
   - Go to [GitHub](https://github.com) and sign in to your account

2. **Access GitHub's Import Repository Page**:
   - Go to [https://github.com/new/import](https://github.com/new/import)

3. **Enter Repository Details**:
   - In "Your old repository's clone URL" field, enter your Replit project URL:
     ```
     https://replit.com/@YourUsername/ProjectName
     ```
   - Give your repository a name (e.g., "telegram-forwarder-bot")
   - Choose public or private visibility
   - Click "Begin import"

4. **Wait for Import**:
   - GitHub will process the import (this may take a few minutes)
   - You'll receive a notification when complete

### Method 2: Using the provided push_to_github.sh script

1. **Create a New Empty GitHub Repository**:
   - Go to [https://github.com/new](https://github.com/new)
   - Create a new repository WITHOUT initializing it (no README, .gitignore, or license)
   - Take note of the repository URL

2. **Run the Push Script**:
   - Open the Replit Shell/Console
   - Run the script, replacing with your information:
     ```bash
     ./push_to_github.sh your-github-username your-repository-name
     ```
   - Follow the on-screen instructions

3. **Verify**:
   - Check your GitHub account to confirm the code was pushed

### Method 3: Manual Git Commands

If you prefer to use Git commands directly:

```bash
# Initialize a Git repository
git init

# Add all files
git add .

# Commit changes
git commit -m "Initial commit"

# Add the GitHub remote
git remote add origin https://github.com/your-username/your-repo-name.git

# Push to GitHub
git push -u origin main
```

## Choosing a Deployment Platform

After importing to GitHub, you can deploy the bot on various platforms. Each has its own advantages:

| Platform | Advantages | Free Tier | Database Included |
|----------|------------|-----------|------------------|
| Koyeb    | Easy to use, good performance | Limited | Yes |
| Heroku   | Well-established, easy to use | Limited | Yes |
| Railway  | Developer-friendly, simple | Yes | Yes |
| Replit   | All-in-one solution, easy to use | Yes | Yes |
| VPS      | Full control, scalable | No | Self-managed |

Detailed deployment instructions for each platform are available in the [deploy/](deploy/) directory.

## Quick Reference for Different Deployment Options

### Koyeb Deployment
See [deploy/koyeb.md](deploy/koyeb.md) for detailed instructions

### Heroku Deployment
See [deploy/heroku.md](deploy/heroku.md) for detailed instructions

### Railway Deployment
See [deploy/railway.md](deploy/railway.md) for detailed instructions

### Replit Deployment
See [deploy/replit.md](deploy/replit.md) for detailed instructions

### VPS Deployment
See [deploy/vps.md](deploy/vps.md) for detailed instructions

## Environment Variables

All platforms require the following environment variables:

```
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

Plus database connection details (varies by platform).

## Keeping Your Bot Running 24/7

To ensure 24/7 operation, consider:

1. Use a paid tier on your chosen platform
2. Set up health check monitoring:
   - Create an account on [Hetrix Tools](https://hetrixtools.com/) or [UptimeRobot](https://uptimerobot.com/)
   - Add a monitor that pings your app's `/health` endpoint every 5 minutes

## Troubleshooting

- **Import Fails**: Try cleaning the repository before importing (remove unnecessary files)
- **Deployment Fails**: Check the logs on your platform for specific error messages
- **Bot Not Responding**: Verify environment variables are correctly set
- **Database Connection Issues**: Confirm database credentials and connection string

## Support

For help with deployment issues:
- Check the platform's documentation
- Refer to the detailed guides in the [deploy/](deploy/) directory
- Search for specific error messages online