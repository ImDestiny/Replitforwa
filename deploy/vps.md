# Deploying on a VPS (Virtual Private Server)

This guide will help you deploy the Telegram Advanced Message Forwarder on your own Virtual Private Server (VPS) such as DigitalOcean, AWS EC2, Linode, or any other Linux-based server.

## Prerequisites

- A VPS running Ubuntu 20.04 or newer
- Root access or sudo privileges
- Domain name (optional, but recommended for HTTPS)

## Deployment Steps

### 1. Update the System

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Required Dependencies

```bash
# Install Python and other dependencies
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx

# Install system dependencies for Python libraries
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev
```

### 3. Create a PostgreSQL Database

```bash
# Access PostgreSQL
sudo -u postgres psql

# Create a new database and user
CREATE DATABASE forwarderbot;
CREATE USER botuser WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE forwarderbot TO botuser;
\q

# Test the connection
psql -h localhost -U botuser -d forwarderbot
# Enter the password when prompted
```

### 4. Set Up the Application

```bash
# Create a user for the application (optional)
sudo adduser --system --group botuser
sudo usermod -aG sudo botuser

# Create application directory
sudo mkdir -p /opt/telegram-forwarder
sudo chown botuser:botuser /opt/telegram-forwarder

# Switch to the application user
sudo su - botuser

# Clone the repository
cd /opt/telegram-forwarder
git clone https://github.com/your-username/your-repo.git .

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the application directory:

```bash
nano /opt/telegram-forwarder/.env
```

Add the following content:

```
API_ID=your_api_id
API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
BOT_OWNER_ID=your_telegram_id
DATABASE_URL=postgresql://botuser:your_secure_password@localhost/forwarderbot
PGDATABASE=forwarderbot
PGUSER=botuser
PGPASSWORD=your_secure_password
PGHOST=localhost
PGPORT=5432
FORCE_SUB_CHANNEL=your_channel_username (optional)
FORCE_SUB_ON=FALSE (optional)
```

Save and exit (Ctrl+X, then Y, then Enter).

### 6. Set Up Systemd Service

Create a service file:

```bash
sudo nano /etc/systemd/system/telegram-forwarder.service
```

Add the following content:

```ini
[Unit]
Description=Telegram Advanced Message Forwarder
After=network.target postgresql.service

[Service]
User=botuser
Group=botuser
WorkingDirectory=/opt/telegram-forwarder
Environment="PATH=/opt/telegram-forwarder/venv/bin"
EnvironmentFile=/opt/telegram-forwarder/.env
ExecStart=/opt/telegram-forwarder/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 1 main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and exit the editor.

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-forwarder
sudo systemctl start telegram-forwarder
```

Check the status:

```bash
sudo systemctl status telegram-forwarder
```

### 7. Set Up Nginx as a Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/telegram-forwarder
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain or server IP

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Create a symbolic link to enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/telegram-forwarder /etc/nginx/sites-enabled/
```

Test and restart Nginx:

```bash
sudo nginx -t
sudo systemctl restart nginx
```

### 8. Set Up SSL with Let's Encrypt (Optional but Recommended)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

Follow the prompts to complete the SSL setup.

### 9. Set Up Monitoring (Optional)

You might want to monitor your application with a tool like Hetrix Tools or UptimeRobot.

For Hetrix Tools:
1. Create an account on [Hetrix Tools](https://hetrixtools.com/)
2. Add a new uptime monitor with your domain
3. Use the `/health` endpoint for monitoring: `https://your-domain.com/health`

### 10. Set Up Automatic Updates (Optional)

To keep your system updated:

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Updating the Application

To update your application when there are new changes:

```bash
cd /opt/telegram-forwarder
sudo su - botuser
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart telegram-forwarder
```

## Backup and Restore

### Backup Database

```bash
pg_dump -U botuser -d forwarderbot > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
psql -U botuser -d forwarderbot < backup_file.sql
```

## Troubleshooting

- **Service Not Starting**: Check logs with `sudo journalctl -u telegram-forwarder`
- **Nginx Issues**: Check logs with `sudo tail -f /var/log/nginx/error.log`
- **Database Connection Problems**: Verify PostgreSQL is running with `sudo systemctl status postgresql`
- **Permission Issues**: Ensure proper file ownership with `sudo chown -R botuser:botuser /opt/telegram-forwarder`

For more advanced troubleshooting, consult the error logs and refer to the project's GitHub repository.