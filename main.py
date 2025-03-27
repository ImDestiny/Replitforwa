# Advanced Telegram Forwarder Bot
# Main Flask application to serve UI and run the bot

import os
import subprocess
import threading
import time
from flask import Flask, render_template, jsonify, redirect, url_for
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "telegram-forwarder-secret")

# Bot process reference
bot_process = None

def start_bot():
    """Start the Telegram bot process"""
    global bot_process
    if bot_process is None or bot_process.poll() is not None:
        logger.info("Starting bot process...")
        bot_process = subprocess.Popen(
            ["python", "new_bot/main.py"],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        logger.info(f"Bot process started with PID: {bot_process.pid}")
        
        # Start thread to monitor bot output
        threading.Thread(target=monitor_bot_output, daemon=True).start()
    else:
        logger.info("Bot already running")

def monitor_bot_output():
    """Monitor the bot's output and log it"""
    global bot_process
    if bot_process:
        for line in bot_process.stdout:
            logger.info(f"Bot: {line.decode().strip()}")
        for line in bot_process.stderr:
            logger.error(f"Bot error: {line.decode().strip()}")
            
def stop_bot():
    """Stop the Telegram bot process"""
    global bot_process
    if bot_process and bot_process.poll() is None:
        logger.info("Stopping bot process...")
        bot_process.terminate()
        try:
            bot_process.wait(timeout=5)
            logger.info("Bot process stopped")
        except subprocess.TimeoutExpired:
            logger.warning("Bot process didn't terminate, forcing...")
            bot_process.kill()
        bot_process = None
    else:
        logger.info("No bot process to stop")

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/start_bot', methods=['POST'])
def start_bot_endpoint():
    """Endpoint to start the bot"""
    start_bot()
    return jsonify({"status": "success", "message": "Bot started"})

@app.route('/stop_bot', methods=['POST'])  
def stop_bot_endpoint():
    """Endpoint to stop the bot"""
    stop_bot()
    return jsonify({"status": "success", "message": "Bot stopped"})

@app.route('/bot_status')
def bot_status():
    """Check if the bot is running"""
    global bot_process
    is_running = bot_process is not None and bot_process.poll() is None
    return jsonify({
        "status": "running" if is_running else "stopped"
    })

@app.route('/health')
def health():
    """Health check endpoint for monitoring services."""
    return jsonify({
        "status": "ok",
        "bot_running": bot_process is not None and bot_process.poll() is None
    })

if __name__ == '__main__':
    try:
        # Start the bot on application startup
        start_bot()
        # Run the Flask application
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        # Make sure we clean up the bot process when Flask exits
        stop_bot()