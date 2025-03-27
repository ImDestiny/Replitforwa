import os
import logging
import threading
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from bot_manager import BotManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Bot Manager instance
bot_manager = BotManager()

@app.route('/')
def index():
    if 'user_phone' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        api_id = request.form.get('api_id')
        api_hash = request.form.get('api_hash')
        
        if not phone or not api_id or not api_hash:
            flash('Please fill in all required fields', 'danger')
            return render_template('login.html')
        
        session['user_phone'] = phone
        session['api_id'] = api_id
        session['api_hash'] = api_hash
        
        # Initialize the bot for this user
        try:
            result = bot_manager.initialize_bot(phone, int(api_id), api_hash)
            if result.get('needs_code'):
                flash('Please check your Telegram app for the verification code', 'warning')
                return render_template('login.html', awaiting_code=True, phone=phone)
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash(f'Error logging in: {str(e)}', 'danger')
            session.pop('user_phone', None)
            session.pop('api_id', None)
            session.pop('api_hash', None)
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/submit_code', methods=['POST'])
def submit_code():
    if 'user_phone' not in session:
        flash('Session expired, please login again', 'danger')
        return redirect(url_for('login'))
    
    code = request.form.get('code')
    phone = session.get('user_phone')
    
    if not code:
        flash('Please enter the verification code', 'danger')
        return render_template('login.html', awaiting_code=True, phone=phone)
    
    try:
        result = bot_manager.submit_code(phone, code)
        if result.get('success'):
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(f'Error: {result.get("error", "Unknown error")}', 'danger')
            return render_template('login.html', awaiting_code=True, phone=phone)
    except Exception as e:
        logger.error(f"Code submission error: {str(e)}")
        flash(f'Error: {str(e)}', 'danger')
        return render_template('login.html', awaiting_code=True, phone=phone)

@app.route('/dashboard')
def dashboard():
    if 'user_phone' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    phone = session.get('user_phone')
    user_data = bot_manager.get_user_data(phone)
    
    return render_template(
        'dashboard.html',
        user_data=user_data,
        active_task=bot_manager.get_active_task(phone),
        forwarding_status=bot_manager.get_forwarding_status(phone)
    )

@app.route('/add_source', methods=['POST'])
def add_source():
    if 'user_phone' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    source_link = request.form.get('source_link')
    phone = session.get('user_phone')
    
    if not source_link:
        return jsonify({'success': False, 'error': 'No source link provided'})
    
    try:
        result = bot_manager.add_source(phone, source_link)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Add source error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/add_destination', methods=['POST'])
def add_destination():
    if 'user_phone' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    destination_link = request.form.get('destination_link')
    phone = session.get('user_phone')
    
    if not destination_link:
        return jsonify({'success': False, 'error': 'No destination link provided'})
    
    try:
        result = bot_manager.add_destination(phone, destination_link)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Add destination error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/set_last_message', methods=['POST'])
def set_last_message():
    if 'user_phone' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    source_id = request.form.get('source_id')
    last_message_link = request.form.get('last_message_link')
    phone = session.get('user_phone')
    
    if not source_id or not last_message_link:
        return jsonify({'success': False, 'error': 'Missing required fields'})
    
    try:
        result = bot_manager.set_last_message(phone, source_id, last_message_link)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Set last message error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/start_forwarding', methods=['POST'])
def start_forwarding():
    if 'user_phone' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    phone = session.get('user_phone')
    source_id = request.form.get('source_id')
    destination_id = request.form.get('destination_id')
    
    if not source_id or not destination_id:
        return jsonify({'success': False, 'error': 'Missing required fields'})
    
    try:
        # Start forwarding in a separate thread to avoid blocking the web server
        threading.Thread(
            target=bot_manager.start_forwarding,
            args=(phone, source_id, destination_id),
            daemon=True
        ).start()
        
        return jsonify({'success': True, 'message': 'Forwarding started'})
    except Exception as e:
        logger.error(f"Start forwarding error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/cancel_forwarding', methods=['POST'])
def cancel_forwarding():
    if 'user_phone' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    phone = session.get('user_phone')
    
    try:
        result = bot_manager.cancel_forwarding(phone)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Cancel forwarding error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/logout')
def logout():
    phone = session.get('user_phone')
    if phone:
        bot_manager.logout_user(phone)
    
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/status')
def status():
    if 'user_phone' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    phone = session.get('user_phone')
    return jsonify(bot_manager.get_forwarding_status(phone))

@app.route('/delete_source', methods=['POST'])
def delete_source():
    if 'user_phone' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    phone = session.get('user_phone')
    source_id = request.form.get('source_id')
    
    if not source_id:
        return jsonify({'success': False, 'error': 'No source ID provided'})
    
    try:
        result = bot_manager.delete_source(phone, source_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Delete source error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/delete_destination', methods=['POST'])
def delete_destination():
    if 'user_phone' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    phone = session.get('user_phone')
    destination_id = request.form.get('destination_id')
    
    if not destination_id:
        return jsonify({'success': False, 'error': 'No destination ID provided'})
    
    try:
        result = bot_manager.delete_destination(phone, destination_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Delete destination error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Keep the app alive route
@app.route('/health')
def health():
    return 'OK', 200
