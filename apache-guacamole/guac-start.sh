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
