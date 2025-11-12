# chromium-base/Dockerfile
FROM ubuntu:22.04

# Install chromium dependencies (not the chromium binary)
RUN apt-get update && apt-get install -y \
    wget unzip ca-certificates gnupg \
    libnss3 libxss1 libasound2 libatk-bridge2.0-0 libgtk-3-0 \
    libdrm2 libgbm1 libxdamage1 libxcomposite1 libxrandr2 \
    libxkbcommon0 libpango-1.0-0 libx11-xcb1 libxshmfence1 \
    fonts-liberation libappindicator3-1 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/chromium-versions /usr/local/chromium

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

