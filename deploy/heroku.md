# Deploying on Heroku

Heroku is a popular platform-as-a-service that makes it easy to deploy, manage, and scale your applications.

## Prerequisites

- A [Heroku account](https://signup.heroku.com/)
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed on your system
- Git installed on your system
- Your code in a Git repository

## Deployment Steps

### Method 1: Direct Deployment from GitHub

1. **Login to Heroku**
   - Go to [Heroku Dashboard](https://dashboard.heroku.com/)
   - Sign in with your account

2. **Create a New App**
   - Click "New" and select "Create new app"
   - Choose a unique app name
   - Select your region
   - Click "Create app"

3. **Connect to GitHub**
   - In the "Deploy" tab, choose "GitHub" as the deployment method
   - Connect to your GitHub account if not already connected
   - Search for and select your repository

4. **Configure Automatic Deploys (Optional)**
   - Choose the branch to deploy
   - Enable "Automatic Deploys" if you want automatic deployment when you push to the repository

5. **Configure Environment Variables**
   - Go to the "Settings" tab
   - Click "Reveal Config Vars"
   - Add the following variables:
     - `API_ID`: Your Telegram API ID
     - `API_HASH`: Your Telegram API Hash
     - `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token
     - (Optional) `BOT_OWNER_ID`: Telegram user ID of the bot owner(s)
     - (Optional) `FORCE_SUB_CHANNEL`: Channel username for forced subscription feature
     - (Optional) `FORCE_SUB_ON`: Set to "TRUE" to enable forced subscription

6. **Add a PostgreSQL Database**
   - In the "Resources" tab, search for "Heroku Postgres" under Add-ons
   - Select a plan (Hobby Dev is free) and submit the order
   - Heroku will automatically add the `DATABASE_URL` environment variable

7. **Deploy**
   - In the "Deploy" tab, scroll down to "Manual deploy"
   - Click "Deploy Branch"
   - Wait for the build and deployment to complete

8. **View Your App**
   - Click "Open app" to view your deployed application

### Method 2: Deployment via Heroku CLI

1. **Login to Heroku CLI**
   ```
   heroku login
   ```

2. **Create a Heroku App**
   ```
   heroku create your-app-name
   ```

3. **Add PostgreSQL Add-on**
   ```
   heroku addons:create heroku-postgresql:hobby-dev
   ```

4. **Set Environment Variables**
   ```
   heroku config:set API_ID=your_api_id
   heroku config:set API_HASH=your_api_hash
   heroku config:set TELEGRAM_BOT_TOKEN=your_bot_token
   heroku config:set BOT_OWNER_ID=your_telegram_id
   ```

5. **Push Your Code to Heroku**
   ```
   git push heroku main
   ```

6. **Open Your App**
   ```
   heroku open
   ```

## Scaling

Heroku's free tier puts your app to sleep after 30 minutes of inactivity. To keep your bot running 24/7:

1. Upgrade to a paid dyno or use a service like UptimeRobot to ping your app regularly.
2. Use the `/health` endpoint of your app for monitoring.

```
# Example with UptimeRobot
https://your-app-name.herokuapp.com/health
```

## Troubleshooting

- **Application Error**: Check the logs with `heroku logs --tail`
- **H10 - App Crashed**: Verify that your Procfile is correct and all required dependencies are in requirements.txt
- **H12 - Request Timeout**: Your app might be taking too long to process a request, optimize your code

For more help, refer to the [Heroku Dev Center](https://devcenter.heroku.com/) or contact Heroku support.