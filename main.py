import os
import logging
import subprocess
from flask import Flask, jsonify

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Add file handler
logger = logging.getLogger(__name__)
if not os.path.exists('logs'):
    os.makedirs('logs')
file_handler = logging.FileHandler('logs/app.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Create Flask app
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    """Main page."""
    return "Telegram Forwarder Bot is running. The bot is accessible via Telegram."

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for monitoring services."""
    # Try to check if the bot is running
    try:
        with open('logs/bot.log', 'r') as f:
            bot_logs = f.read()
            bot_running = "Telegram Bot started successfully!" in bot_logs
    except:
        bot_running = False
    
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'bot_running': bot_running
    })

# Start the bot process when the application starts
try:
    # Start the bot in a separate process
    subprocess.Popen(['python', 'run_bot.py'], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE)
    logger.info("Started bot process")
except Exception as e:
    logger.error(f"Error starting bot process: {e}")

if __name__ == "__main__":
    # Start the Flask app
    app.run(host="0.0.0.0", port=5000, debug=True)