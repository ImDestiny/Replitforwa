# Deploying on Koyeb

Koyeb is a developer-friendly serverless platform that offers an easy way to deploy your application.

## Prerequisites

- A [Koyeb account](https://app.koyeb.com/)
- Your code pushed to a GitHub repository

## Deployment Steps

1. **Login to Koyeb**
   - Go to the [Koyeb Control Panel](https://app.koyeb.com/)
   - Sign in with your account

2. **Create a New App**
   - Click on "Create App"
   - Select "GitHub" as your deployment method
   - Connect to your GitHub account if you haven't already
   - Select the repository containing this project

3. **Configure the App**
   - **Name**: Give your app a name (e.g., "telegram-forwarder")
   - **Region**: Choose a server region close to you
   - **Instance Type**: Select the instance type based on your needs (Nano is sufficient for most use cases)
   - **Branch**: Select the branch to deploy (usually `main` or `master`)
   - **Build Command**: Leave as default (Koyeb will detect it's a Python app)
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --reuse-port --workers 1 main:app`

4. **Set Environment Variables**
   
   Click on "Environment" and add the following environment variables:
   
   - `API_ID`: Your Telegram API ID
   - `API_HASH`: Your Telegram API Hash
   - `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token
   - `DATABASE_URL`: Your PostgreSQL database URL (Koyeb can provide a database add-on)
   - `PGDATABASE`: PostgreSQL database name (if using Koyeb's database)
   - `PGUSER`: PostgreSQL username (if using Koyeb's database)
   - `PGPASSWORD`: PostgreSQL password (if using Koyeb's database)
   - `PGHOST`: PostgreSQL host (if using Koyeb's database)
   - `PGPORT`: PostgreSQL port (if using Koyeb's database)
   - `BOT_OWNER_ID`: Telegram user ID of the bot owner(s), comma-separated for multiple IDs
   - (Optional) `FORCE_SUB_CHANNEL`: Channel username for forced subscription feature
   - (Optional) `FORCE_SUB_ON`: Set to "TRUE" to enable forced subscription

5. **Deploy**
   - Click "Deploy" to start the deployment process

6. **Monitor Deployment**
   - Koyeb will build and deploy your application
   - You can monitor the process in the "Deployments" tab

7. **Access Your App**
   - Once deployed, your app will be available at `https://app-name.koyeb.app`
   - Open this URL in your browser to access the web dashboard

8. **Set Up Persistent Storage (Optional)**
   - If you need persistent storage for session files:
     - Go to the "Storage" tab in your app settings
     - Add a Volume for the `/sessions` directory

## Updating Your App

When you push changes to your GitHub repository, Koyeb will automatically deploy the updates, ensuring your app is always running the latest version.

## Troubleshooting

- **Deployment Failure**: Check the logs in the "Deployments" tab for error details
- **App Not Responding**: Verify your environment variables are correctly set
- **Database Connection Issues**: Ensure your database credentials are correct and the database is accessible

For more help, refer to the [Koyeb Documentation](https://www.koyeb.com/docs) or contact Koyeb support.