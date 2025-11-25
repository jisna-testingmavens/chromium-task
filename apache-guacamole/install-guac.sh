#!/usr/bin/env bash
# =================================================
# Apache Guacamole 1.6.0 Installer (Ubuntu 22/24)
# With JSON Auth + 5 Virtual VNC Displays
# Uses Tomcat10 (compatible with Guacamole)
# =================================================

set -e

GUAC_VERSION="1.6.0"
JSON_EXT="guacamole-auth-json-${GUAC_VERSION}.tar.gz"

echo "🚀 Updating system..."
sudo apt update -y
sudo apt upgrade -y

echo "📦 Installing dependencies..."
sudo apt install -y build-essential libcairo2-dev libjpeg-turbo8-dev libpng-dev \
    libtool-bin libossp-uuid-dev libvncserver-dev freerdp2-dev libpango1.0-dev \
    libssh2-1-dev libtelnet-dev libpulse-dev libssl-dev libvorbis-dev libwebp-dev \
    xvfb x11vnc wget net-tools tomcat10

# =================================================
# BUILD & INSTALL guacd
# =================================================
echo "📥 Downloading guacamole-server..."
wget "https://apache.org/dyn/closer.lua/guacamole/${GUAC_VERSION}/source/guacamole-server-${GUAC_VERSION}.tar.gz?action=download" \
    -O guacamole-server-${GUAC_VERSION}.tar.gz

echo "📦 Extracting..."
tar -xzf guacamole-server-${GUAC_VERSION}.tar.gz
cd guacamole-server-${GUAC_VERSION}

echo "🔧 Configuring guacd..."
./configure --with-init-dir=/etc/init.d

echo "⚙️ Compiling guacd..."
make -j$(nproc)

echo "📥 Installing guacd..."
sudo make install
sudo ldconfig
cd ..
sudo systemctl enable guacd

# =================================================
# INSTALL GUACAMOLE WEBAPP
# =================================================
echo "📥 Downloading Guacamole webapp..."
wget "https://archive.apache.org/dist/guacamole/${GUAC_VERSION}/binary/guacamole-${GUAC_VERSION}.war"

echo "📦 Deploying guacamole.war into Tomcat..."
sudo mv guacamole-${GUAC_VERSION}.war /var/lib/tomcat10/webapps/guacamole.war

# =================================================
# INSTALL JSON AUTH EXTENSION
# =================================================
echo "📥 Downloading JSON Authentication Extension..."
wget "https://apache.org/dyn/closer.lua/guacamole/${GUAC_VERSION}/binary/${JSON_EXT}?action=download" \
    -O ${JSON_EXT}

echo "📦 Extracting JSON Auth Extension..."
tar -xzf ${JSON_EXT}
sudo mkdir -p /etc/guacamole/extensions
sudo cp guacamole-auth-json-${GUAC_VERSION}/guacamole-auth-json-${GUAC_VERSION}.jar /etc/guacamole/extensions/

# =================================================
# CREATE CORE CONFIGURATION
# =================================================
echo "📝 Writing guacamole.properties..."
sudo mkdir -p /etc/guacamole

sudo tee /etc/guacamole/guacamole.properties >/dev/null <<'EOF'
auth-provider: org.apache.guacamole.auth.json.JSONAuthenticationProvider
json-secret-key: "replace-this-secret-key"
json-authorization-endpoint: http://localhost:8080/guacamole/api
guacd-hostname: localhost
guacd-port: 4822
EOF

# =================================================
# USER-MAPPING (OPTIONAL fallback login)
# =================================================
sudo tee /etc/guacamole/user-mapping.xml >/dev/null <<'EOF'
<user-mapping>
  <authorize username="test" password="test">
    <connection name="Display-5900">
      <protocol>vnc</protocol>
      <param name="hostname">localhost</param>
      <param name="port">5900</param>
    </connection>
  </authorize>
</user-mapping>
EOF

# =================================================
# CREATE VNC START SCRIPT (5 Virtual Displays)
# =================================================
echo "📝 Creating guac-start.sh..."

sudo tee ./guac-start.sh >/dev/null <<'EOF'
#!/usr/bin/env bash
echo "🚀 Starting virtual VNC displays (ports 5900–5904)..."

for i in {0..4}; do
  DISPLAY_NUM=$((i + 1))
  PORT=$((5900 + i))
  echo "🖥️ Display :$DISPLAY_NUM on port $PORT"
  Xvfb :$DISPLAY_NUM -screen 0 1024x768x16 &
  x11vnc -display :$DISPLAY_NUM -rfbport $PORT -forever -shared -nopw &
done

echo "🔁 Restarting guacd and Tomcat10..."
sudo systemctl restart guacd
sudo systemctl restart tomcat10

echo "✅ All services running!"
EOF

chmod +x ./guac-start.sh

# =================================================
# ENABLE SERVICES
# =================================================
sudo systemctl enable tomcat10
sudo systemctl daemon-reload

echo ""
echo "=============================================================="
echo "✅ Apache Guacamole ${GUAC_VERSION} Installation Complete!"
echo "📌 Next steps:"
echo "   1. EDIT /etc/guacamole/guacamole.properties"
echo "      → Replace json-secret-key with a secure HEX key"
echo "   2. Run:  ./guac-start.sh"
echo "   3. Open in browser:"
echo "      👉 http://<SERVER-IP>:8080/guacamole/"
echo "=============================================================="

