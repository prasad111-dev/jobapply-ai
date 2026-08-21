#!/bin/bash
# JobApply AI — AWS EC2 Setup Script
# Run on a fresh Ubuntu 22.04 / 24.04 LTS instance (t2.micro works)
# Usage: ssh into your EC2, then:
#   curl -fsSL https://raw.githubusercontent.com/your-repo/main/aws_setup.sh | bash
# Or upload and run: bash aws_setup.sh

set -euo pipefail

APP_DIR="/opt/jobapply"
REPO="https://github.com/prasad111-dev/jobapply-ai.git"
BRANCH="main"

echo "========================================="
echo " JobApply AI — AWS EC2 Setup"
echo "========================================="

# ── 1. System packages ──────────────────────────────────────────────
echo "[1/7] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
  python3.11 python3.11-venv python3.11-dev python3-pip \
  nodejs npm \
  nginx \
  chromium-browser \
  libnss3 libatk-bridge2.0-0 libx11-xcb1 libxcomposite1 \
  libxdamage1 libxrandr2 libgbm1 libasound2 libpangocairo-1.0-0 \
  libgtk-3-0 libxss1 libxtst6 fonts-liberation \
  wget git curl

echo "  ✓ System packages installed"

# ── 2. Clone app ────────────────────────────────────────────────────
echo "[2/7] Cloning app..."
sudo rm -rf "$APP_DIR"
sudo git clone --branch "$BRANCH" "$REPO" "$APP_DIR"
sudo chown -R $USER:$USER "$APP_DIR"
cd "$APP_DIR"

echo "  ✓ App cloned to $APP_DIR"

# ── 3. Python venv + deps ───────────────────────────────────────────
echo "[3/7] Setting up Python environment..."
python3.11 -m venv backend/venv
source backend/venv/bin/activate
pip install --upgrade pip -q
pip install -r backend/requirements.txt -q
pip install playwright -q
playwright install chromium

echo "  ✓ Python env ready"

# ── 4. Frontend build ───────────────────────────────────────────────
echo "[4/7] Building frontend..."
cd "$APP_DIR/frontend"
npm ci --silent
npm run build
cd "$APP_DIR"

echo "  ✓ Frontend built"

# ── 5. Environment file ─────────────────────────────────────────────
echo "[5/7] Creating .env..."
if [ ! -f "$APP_DIR/backend/.env" ]; then
  SECRET_KEY=$(python3.11 -c "import secrets; print(secrets.token_hex(32))")
  cat > "$APP_DIR/backend/.env" <<EOF
# === JobApply AI — Environment ===
MONGODB_URL=mongodb+srv://karishama:karishama@cluster0.db3u0sh.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=jobapply
SECRET_KEY=$SECRET_KEY
ENVIRONMENT=production
FRONTEND_URL=http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR_EC2_IP")

# JSearch API (get free key from https://app.openwebninja.com/api/jsearch)
JSEARCH_API_KEY=

# Optional: Admin emails to auto-promote
EXTRA_ADMIN_EMAILS=["prasadghavghave0@gmail.com","prasadghavghave0@gmil.com"]
EOF
  echo "  ✓ .env created — edit $APP_DIR/backend/.env to add JSEARCH_API_KEY"
else
  echo "  ✓ .env already exists, skipping"
fi

# ── 6. Systemd service ─────────────────────────────────────────────
echo "[6/7] Setting up systemd service..."
sudo tee /etc/systemd/system/jobapply.service > /dev/null <<EOF
[Unit]
Description=JobApply AI Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR/backend
Environment=PATH=$APP_DIR/backend/venv/bin:/usr/bin
ExecStart=$APP_DIR/backend/venv/bin/gunicorn app.main:app \\
  --workers 2 \\
  --worker-class uvicorn.workers.UvicornWorker \\
  --bind 127.0.0.1:8000 \\
  --timeout 120 \\
  --access-logfile /var/log/jobapply-access.log \\
  --error-logfile /var/log/jobapply-error.log
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo touch /var/log/jobapply-access.log /var/log/jobapply-error.log
sudo chown $USER:$USER /var/log/jobapply-*.log
sudo systemctl daemon-reload
sudo systemctl enable jobapply
sudo systemctl start jobapply

echo "  ✓ Service started"

# ── 7. Nginx reverse proxy ─────────────────────────────────────────
echo "[7/7] Configuring Nginx..."
sudo tee /etc/nginx/sites-available/jobapply > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}
EOF

sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/jobapply /etc/nginx/sites-enabled/jobapply
sudo nginx -t
sudo systemctl restart nginx

echo "  ✓ Nginx configured"

# ── Done ────────────────────────────────────────────────────────────
EC2_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR_EC2_IP")
echo ""
echo "========================================="
echo " ✅ DEPLOYMENT COMPLETE"
echo "========================================="
echo ""
echo " App URL:    http://$EC2_IP"
echo " App dir:    $APP_DIR"
echo " Service:    sudo systemctl status jobapply"
echo " Logs:       sudo journalctl -u jobapply -f"
echo " Restart:    sudo systemctl restart jobapply"
echo ""
echo " Next steps:"
echo "  1. Edit $APP_DIR/backend/.env to add JSEARCH_API_KEY"
echo "  2. Restart: sudo systemctl restart jobapply"
echo "  3. Open http://$EC2_IP in your browser"
echo ""
