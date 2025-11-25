import json
import hmac
import hashlib
import time
import base64
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
 
# === CONFIG ===
secret_key_hex = '28169799454fdfb2870d65374a4ed0f2'
secret_key = bytes.fromhex(secret_key_hex)
iv = b'\x00' * 16  # static IV for Guacamole JSON auth
 
user_data = {
    "username": "test_user",
    "expires": int(time.time() * 1000) + 3600 * 1000 *24 * 365,
    "connections": {
        "vnc-display-14": {
            "protocol": "vnc",
            "parameters": {
                "hostname": "127.0.0.1",
                "port": "5914",
                "password": "",
                "color-depth": "24",
                "enable-audio": "false"
            }
        }
    }
}
 
 
 
# === STEP 2: Sign ===
json_data = json.dumps(user_data)
signature = hmac.new(secret_key, json_data.encode(), hashlib.sha256).digest()
signed_data = signature + json_data.encode()
 
# === STEP 3: Encrypt (AES CBC) ===
padder = padding.PKCS7(algorithms.AES.block_size).padder()
padded = padder.update(signed_data) + padder.finalize()
 
cipher = Cipher(algorithms.AES(secret_key), modes.CBC(iv), backend=default_backend())
encryptor = cipher.encryptor()
encrypted = encryptor.update(padded) + encryptor.finalize()
 
# === STEP 4: Base64 encode ===
payload = base64.b64encode(encrypted).decode()
 
# === STEP 5: Send to Guacamole ===
url = "http://localhost:8080/guacamole/api/tokens"
headers = {"Content-Type": "application/x-www-form-urlencoded"}
data = {"data": payload}
 
print(f"Sending request to {url}...\n")
response = requests.post(url, headers=headers, data=data)
 
print("Status Code:", response.status_code)
try:
    print("Response:", response.json())
except Exception:
    print("Raw Response:", response.text)
 
