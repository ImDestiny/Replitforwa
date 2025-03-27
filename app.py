from flask import Flask, render_template, jsonify, redirect, url_for, request, session, flash

app = Flask(__name__)
app.secret_key = "telegram-forwarder-secret"

@app.route('/')
def home():
    return """
    <html>
    <head>
        <title>Telegram Message Forwarder</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #3498db; }
            .card { border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin-bottom: 20px; }
            .btn { display: inline-block; background: #3498db; color: white; padding: 10px 15px; 
                   text-decoration: none; border-radius: 4px; margin-right: 10px; }
            .btn:hover { background: #2980b9; }
            .feature { margin-bottom: 10px; }
        </style>
    </head>
    <body>
        <h1>Telegram Message Forwarder</h1>
        <div class="card">
            <h2>Welcome to the Telegram Message Forwarder</h2>
            <p>This application allows you to forward messages between Telegram channels with advanced features.</p>
            <a href="/login" class="btn">Login with Telegram</a>
        </div>
        
        <div class="card">
            <h2>Features</h2>
            <div class="feature">✓ Forward messages from one channel to another</div>
            <div class="feature">✓ Resume interrupted forwarding tasks</div>
            <div class="feature">✓ Rate-limited forwarding (1 message every 3 seconds)</div>
            <div class="feature">✓ Support for private and restricted channels</div>
            <div class="feature">✓ Easy-to-use web interface</div>
        </div>
    </body>
    </html>
    """

@app.route('/login')
def login():
    return """
    <html>
    <head>
        <title>Login - Telegram Message Forwarder</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #3498db; }
            .card { border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin-bottom: 20px; }
            .btn { display: inline-block; background: #3498db; color: white; padding: 10px 15px; 
                   text-decoration: none; border-radius: 4px; margin-right: 10px; }
            .btn:hover { background: #2980b9; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; }
            input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            .btn-back { background: #95a5a6; }
            .btn-back:hover { background: #7f8c8d; }
        </style>
    </head>
    <body>
        <h1>Login with Telegram</h1>
        <div class="card">
            <form action="/dashboard" method="GET">
                <div class="form-group">
                    <label for="phone">Phone Number (with country code)</label>
                    <input type="text" id="phone" name="phone" placeholder="+1234567890" required>
                </div>
                <div class="form-group">
                    <label for="api_id">API ID</label>
                    <input type="text" id="api_id" name="api_id" placeholder="12345678" required>
                </div>
                <div class="form-group">
                    <label for="api_hash">API Hash</label>
                    <input type="text" id="api_hash" name="api_hash" placeholder="abcdef1234567890" required>
                </div>
                <button type="submit" class="btn">Login</button>
                <a href="/" class="btn btn-back">Back</a>
            </form>
        </div>
    </body>
    </html>
    """

@app.route('/dashboard')
def dashboard():
    phone = request.args.get('phone', '')
    return f"""
    <html>
    <head>
        <title>Dashboard - Telegram Message Forwarder</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }}
            h1, h2 {{ color: #3498db; }}
            .card {{ border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin-bottom: 20px; }}
            .btn {{ display: inline-block; background: #3498db; color: white; padding: 10px 15px; 
                   text-decoration: none; border-radius: 4px; margin-right: 10px; }}
            .btn:hover {{ background: #2980b9; }}
            .btn-danger {{ background: #e74c3c; }}
            .btn-danger:hover {{ background: #c0392b; }}
            .row {{ display: flex; flex-wrap: wrap; margin: 0 -10px; }}
            .col {{ flex: 1; padding: 0 10px; min-width: 300px; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; }}
            input, select {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }}
            .status {{ padding: 15px; border-radius: 4px; background: #f8f9fa; }}
            .card-header {{ font-weight: bold; margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <h1>Dashboard</h1>
        <p>Welcome, {phone}</p>
        
        <div class="row">
            <div class="col">
                <div class="card">
                    <div class="card-header">Forwarding Status</div>
                    <div class="status">
                        <p>No active forwarding task.</p>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">Start New Forwarding</div>
                    <form>
                        <div class="form-group">
                            <label for="source">Source</label>
                            <select id="source">
                                <option value="" disabled selected>Select a source</option>
                                <option value="1">Example Channel</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="destination">Destination</label>
                            <select id="destination">
                                <option value="" disabled selected>Select a destination</option>
                                <option value="1">My Channel</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="last-message">Last Message Link (Optional)</label>
                            <input type="text" id="last-message" placeholder="https://t.me/c/123456789/100">
                        </div>
                        <button type="button" class="btn">Start Forwarding</button>
                    </form>
                </div>
            </div>
            
            <div class="col">
                <div class="card">
                    <div class="card-header">Add Source</div>
                    <form>
                        <div class="form-group">
                            <label for="source-link">Source Channel/Group Link</label>
                            <input type="text" id="source-link" placeholder="https://t.me/channel">
                        </div>
                        <button type="button" class="btn">Add Source</button>
                    </form>
                </div>
                
                <div class="card">
                    <div class="card-header">Add Destination</div>
                    <form>
                        <div class="form-group">
                            <label for="destination-link">Destination Channel/Group Link</label>
                            <input type="text" id="destination-link" placeholder="https://t.me/channel">
                        </div>
                        <button type="button" class="btn">Add Destination</button>
                    </form>
                </div>
                
                <div class="card">
                    <div class="card-header">Actions</div>
                    <a href="/" class="btn btn-danger">Logout</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)