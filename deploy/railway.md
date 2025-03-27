# Deploying on Railway

Railway is a modern app hosting platform that makes deployment easy and cost-effective.

## Prerequisites

- A [Railway account](https://railway.app/) (you can sign up with GitHub)
- Your code pushed to a GitHub repository

## Deployment Steps

1. **Login to Railway**
   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Sign in with your GitHub account or other method

2. **Create a New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Select your repository containing this project

3. **Configure Environment Variables**
   - In your project, go to the "Variables" tab
   - Add the following variables:
     - `API_ID`: Your Telegram API ID
     - `API_HASH`: Your Telegram API Hash
     - `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token
     - `BOT_OWNER_ID`: Telegram user ID of the bot owner(s)
     - (Optional) `FORCE_SUB_CHANNEL`: Channel username for forced subscription feature
     - (Optional) `FORCE_SUB_ON`: Set to "TRUE" to enable forced subscription

4. **Add a PostgreSQL Database**
   - Click "New" to add a new service
   - Select "Database" and then "PostgreSQL"
   - Railway will automatically add the database connection variables to your project

5. **Configure the Build Settings (Optional)**
   - Go to the "Settings" tab of your deployment
   - Under "Build & Deploy Settings", you can specify:
     - `START_COMMAND`: `gunicorn --bind 0.0.0.0:$PORT --reuse-port --workers 1 main:app`

6. **Deploy**
   - Railway will automatically deploy your app when you push to the connected GitHub repository
   - You can also manually trigger a deployment from the "Deployments" tab

7. **Generate a Domain**
   - In the "Settings" tab, go to "Domains"
   - Click "Generate Domain" to get a public URL for your app

8. **Monitor Your App**
   - Railway provides logs and metrics in the "Deployments" tab
   - You can monitor CPU, RAM usage, and other metrics

## Persistent Storage

Railway provides ephemeral storage by default, which means files created during runtime will be lost when the app restarts. For persistent storage:

1. Use the PostgreSQL database for storing your data
2. For session files, consider using a cloud storage service or implement database-based session storage

## Updating Your App

Railway automatically deploys new versions when you push to your GitHub repository. You can also manually redeploy from the dashboard.

## Pricing

Railway offers a free tier with limited usage. Check their [pricing page](https://railway.app/pricing) for the latest information. For a production environment, you may need a paid plan.

## Troubleshooting

- **Deployment Failed**: Check the build logs in the "Deployments" tab
- **App Not Running**: Verify that your environment variables are correctly set
- **Database Connection Issues**: Ensure Railway has properly linked the PostgreSQL service to your app

For more help, refer to the [Railway documentation](https://docs.railway.app/) or contact Railway support.