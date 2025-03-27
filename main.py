import os
import json
import logging
import threading
import asyncio
import flask
from flask import Flask, render_template, jsonify, redirect, url_for, request, session, flash
from bot_manager import BotManager

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])

logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "telegram-forwarder-secret")

# Create the bot manager
bot_manager = BotManager()

# Dictionary to track the bot running state
bot_running = {'status': False}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    phone = request.args.get('phone', '')
    api_id = request.args.get('api_id', '')
    api_hash = request.args.get('api_hash', '')
    
    # If we have the credentials, try to initialize the bot
    if phone and api_id and api_hash:
        try:
            result = bot_manager.initialize_bot(phone, api_id, api_hash)
            
            if result['success']:
                if result['needs_code']:
                    # Redirect to code verification page
                    return redirect(url_for('verify_code', phone=phone))
                else:
                    # Bot already authorized, go to dashboard
                    return render_template('dashboard.html', 
                                          phone=phone, 
                                          user_data=bot_manager.get_user_data(phone))
            else:
                flash(f"Error initializing bot: {result.get('error', 'Unknown error')}")
                return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error initializing bot: {str(e)}")
            return redirect(url_for('login'))
    else:
        # If we're missing credentials, redirect to login
        flash("Please provide all required credentials")
        return redirect(url_for('login'))

@app.route('/verify_code')
def verify_code():
    phone = request.args.get('phone', '')
    if not phone:
        flash("Phone number is required")
        return redirect(url_for('login'))
    
    return render_template('verify_code.html', phone=phone)

@app.route('/submit_code', methods=['POST'])
def submit_code():
    phone = request.form.get('phone', '')
    code = request.form.get('code', '')
    
    if not phone or not code:
        flash("Phone number and code are required")
        return redirect(url_for('verify_code', phone=phone))
    
    try:
        result = bot_manager.submit_code(phone, code)
        
        if result['success']:
            # Bot authorized, go to dashboard
            return redirect(url_for('dashboard', phone=phone))
        else:
            flash(f"Error verifying code: {result.get('error', 'Unknown error')}")
            return redirect(url_for('verify_code', phone=phone))
    except Exception as e:
        flash(f"Error verifying code: {str(e)}")
        return redirect(url_for('verify_code', phone=phone))

@app.route('/add_source', methods=['POST'])
def add_source():
    phone = request.form.get('phone', '')
    source_link = request.form.get('source_link', '')
    
    if not phone or not source_link:
        return jsonify({"success": False, "error": "Phone number and source link are required"})
    
    try:
        result = bot_manager.add_source(phone, source_link)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/add_destination', methods=['POST'])
def add_destination():
    phone = request.form.get('phone', '')
    destination_link = request.form.get('destination_link', '')
    
    if not phone or not destination_link:
        return jsonify({"success": False, "error": "Phone number and destination link are required"})
    
    try:
        result = bot_manager.add_destination(phone, destination_link)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/set_last_message', methods=['POST'])
def set_last_message():
    phone = request.form.get('phone', '')
    source_id = request.form.get('source_id', '')
    last_message_link = request.form.get('last_message_link', '')
    
    if not phone or not source_id or not last_message_link:
        return jsonify({"success": False, "error": "Phone number, source ID, and last message link are required"})
    
    try:
        result = bot_manager.set_last_message(phone, source_id, last_message_link)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/start_forwarding', methods=['POST'])
def start_forwarding():
    phone = request.form.get('phone', '')
    source_id = request.form.get('source_id', '')
    destination_id = request.form.get('destination_id', '')
    
    if not phone or not source_id or not destination_id:
        return jsonify({"success": False, "error": "Phone number, source ID, and destination ID are required"})
    
    try:
        # Start the forwarding in a separate thread to avoid blocking the main thread
        threading.Thread(
            target=bot_manager.start_forwarding,
            args=(phone, source_id, destination_id)
        ).start()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/cancel_forwarding', methods=['POST'])
def cancel_forwarding():
    phone = request.form.get('phone', '')
    
    if not phone:
        return jsonify({"success": False, "error": "Phone number is required"})
    
    try:
        result = bot_manager.cancel_forwarding(phone)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_forwarding_status', methods=['GET'])
def get_forwarding_status():
    phone = request.args.get('phone', '')
    
    if not phone:
        return jsonify({"success": False, "error": "Phone number is required"})
    
    try:
        status = bot_manager.get_forwarding_status(phone)
        return jsonify({"success": True, "status": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/logout', methods=['POST'])
def logout():
    phone = request.form.get('phone', '')
    
    if not phone:
        return jsonify({"success": False, "error": "Phone number is required"})
    
    try:
        result = bot_manager.logout_user(phone)
        if result:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Error logging out"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/delete_source', methods=['POST'])
def delete_source():
    phone = request.form.get('phone', '')
    source_id = request.form.get('source_id', '')
    
    if not phone or not source_id:
        return jsonify({"success": False, "error": "Phone number and source ID are required"})
    
    try:
        result = bot_manager.delete_source(phone, source_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/delete_destination', methods=['POST'])
def delete_destination():
    phone = request.form.get('phone', '')
    destination_id = request.form.get('destination_id', '')
    
    if not phone or not destination_id:
        return jsonify({"success": False, "error": "Phone number and destination ID are required"})
    
    try:
        result = bot_manager.delete_destination(phone, destination_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/bot_status', methods=['GET'])
def get_bot_status():
    return jsonify({"status": "running" if bot_running['status'] else "stopped"})

@app.route('/start_bot', methods=['POST'])
def start_bot():
    # Logic to start the Telegram bot
    bot_running['status'] = True
    return jsonify({"message": "Bot started successfully"})

@app.route('/stop_bot', methods=['POST'])
def stop_bot():
    # Logic to stop the Telegram bot
    bot_running['status'] = False
    return jsonify({"message": "Bot stopped successfully"})

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)