from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return """
    <html>
        <head><title>Hello from Telegram Forwarder</title></head>
        <body>
            <h1>Hello from Telegram Forwarder!</h1>
            <p>If you can see this message, the Flask server is working correctly.</p>
        </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)