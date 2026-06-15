FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    xvfb \
    dbus-x11 \
    fluxbox \
    wget \
    curl \
    unzip \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libxshmfence1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install-deps

RUN playwright install chromium

COPY . .

CMD bash -c '\
Xvfb :99 -screen 0 1920x1080x24 & \
export DISPLAY=:99 && \
dbus-daemon --session --fork && \
fluxbox >/dev/null 2>&1 & \
python worker.py'
