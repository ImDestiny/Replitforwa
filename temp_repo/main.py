# bot developer @mr_jisshu
from bot import Bot
from flask import Flask
import threading

app = Bot()  # Initialize the bot

# Flask server for health check
server = Flask(__name__)

@server.route('/')
def health_check():
    return 'Bot is running on Koyeb'

def run_flask():
    server.run(host="0.0.0.0", port=8080)  # Explicitly set port 8080

# Run Flask in a separate thread so it doesn't block the bot
threading.Thread(target=run_flask, daemon=True).start()

# Start the bot
app.run()
