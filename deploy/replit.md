# Deploying on Replit

Replit is a collaborative browser-based IDE that makes it easy to code and deploy applications in one place.

## Prerequisites

- A [Replit account](https://replit.com/signup)

## Deployment Steps

### Method 1: Import from GitHub

1. **Create a New Repl**
   - Go to [Replit Dashboard](https://replit.com/~)
   - Click "Create Repl"
   - Go to "Import from GitHub" tab
   - Paste your GitHub repository URL
   - Select "Python" as the language
   - Click "Import from GitHub"

2. **Configure Environment Variables**
   - In your Repl, click on the lock icon (Secrets) in the left sidebar
   - Add the following secrets:
     - `API_ID`: Your Telegram API ID
     - `API_HASH`: Your Telegram API Hash
     - `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token
     - `BOT_OWNER_ID`: Telegram user ID of the bot owner(s)
     - (Optional) `FORCE_SUB_CHANNEL`: Channel username for forced subscription feature
     - (Optional) `FORCE_SUB_ON`: Set to "TRUE" to enable forced subscription

3. **Add a PostgreSQL Database**
   - In the "Tools" menu, select "Database"
   - Choose "PostgreSQL"
   - Replit will automatically add the database connection variables to your project secrets

4. **Configure Replit to Run the Project**
   - Create a `.replit` file in the root directory with the following content:
   ```
   run = "gunicorn --bind 0.0.0.0:5000 --reuse-port --workers 1 main:app"
   ```
   
   - Also, create a `replit.nix` file if not already present:
   ```nix
   { pkgs }: {
     deps = [
       pkgs.python310
       pkgs.postgresql
       pkgs.replitPackages.prybar-python310
     ];
   }
   ```

5. **Run the Project**
   - Click the "Run" button at the top of the page
   - Replit will install dependencies and start your application

6. **Access Your App**
   - Your app will be available at the URL shown in the webview (typically `https://your-repl-name.your-username.repl.co`)

### Method 2: Start from Scratch

1. **Create a New Repl**
   - Choose "Python" as the template
   - Give your Repl a name

2. **Upload Project Files**
   - You can drag and drop files or use the "Upload file" option
   - Alternatively, use Git commands in the Replit shell:
   ```
   git clone https://github.com/your-username/your-repo.git .
   ```

3. **Follow Steps 2-6 from Method 1**

## Keeping Your App Running 24/7

Replit's free tier has limitations for keeping apps running continuously. To keep your bot running 24/7:

1. **Upgrade to Replit Pro**
   
   OR
   
2. **Use a Service like UptimeRobot**
   - Create an account on [UptimeRobot](https://uptimerobot.com/)
   - Add a new monitor with your Replit app URL (use the `/health` endpoint)
   - Set it to check every 5 minutes
   - This will prevent your Repl from going to sleep

## Troubleshooting

- **Dependencies Not Installing**: Try running `pip install -r requirements.txt` in the Shell
- **App Not Starting**: Check the console for error messages
- **Session Files Issues**: Make sure the session files are being created in the correct directory and have the right permissions
- **Database Connection Errors**: Verify your database connection details in the environment variables

For more help, refer to the [Replit documentation](https://docs.replit.com/) or contact Replit support.