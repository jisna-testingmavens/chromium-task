#!/usr/bin/env python3
import os
import subprocess
import requests
import json
from pathlib import Path

# Chromium versions to download
CHROMIUM_VERSIONS = [
    "120.0.6099.109",
    "119.0.6045.105",
    "118.0.5993.70",
    "117.0.5938.92",
    "116.0.5845.96",
    "115.0.5790.102",
    "114.0.5735.90",
    "113.0.5672.63",
    "112.0.5615.49",
    "111.0.5563.64",
    "110.0.5481.77",
    "109.0.5414.74",
    "108.0.5359.71",
    "107.0.5304.62",
    "106.0.5249.61",
    "105.0.5195.52",
    "104.0.5112.79",
    "103.0.5060.53",
    "102.0.5005.61",
    "101.0.4951.41"
]

BASE_PATH = "/opt/chromium-versions"

# Version to revision mapping (simplified - using approximate revisions)
VERSION_TO_REVISION = {
    "120.0.6099.109": "1217362",
    "119.0.6045.105": "1204232",
    "118.0.5993.70": "1192594",
    "117.0.5938.92": "1181205",
    "116.0.5845.96": "1170107",
    "115.0.5790.102": "1158903",
    "114.0.5735.90": "1135570",
    "113.0.5672.63": "1121455",
    "112.0.5615.49": "1108766",
    "111.0.5563.64": "1097615",
    "110.0.5481.77": "1084008",
    "109.0.5414.74": "1070088",
    "108.0.5359.71": "1056772",
    "107.0.5304.62": "1042082",
    "106.0.5249.61": "1027018",
    "105.0.5195.52": "1012728",
    "104.0.5112.79": "1000137",
    "103.0.5060.53": "992738",
    "102.0.5005.61": "982481",
    "101.0.4951.41": "970830"
}

def download_chromium(version):
    """Download a specific Chromium version"""
    version_path = os.path.join(BASE_PATH, version)
    
    if os.path.exists(version_path) and os.listdir(version_path):
        print(f"✓ Version {version} already exists, skipping...")
        return True
    
    print(f"\n{'='*60}")
    print(f"Downloading Chromium {version}...")
    print(f"{'='*60}")
    
    try:
        os.makedirs(version_path, exist_ok=True)
        
        revision = VERSION_TO_REVISION.get(version)
        if not revision:
            print(f"✗ No revision mapping for version {version}")
            return False
        
        # Download URL for Linux x64
        download_url = f"https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{revision}%2Fchrome-linux.zip?alt=media"
        zip_file = f"{version_path}/chrome-linux.zip"
        
        print(f"Downloading from revision {revision}...")
        print(f"URL: {download_url[:80]}...")
        
        # Download with progress
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024  # 1MB
        downloaded = 0
        
        with open(zip_file, 'wb') as f:
            for data in response.iter_content(block_size):
                downloaded += len(data)
                f.write(data)
                if total_size > 0:
                    percent = int((downloaded / total_size) * 100)
                    print(f"\rProgress: {percent}% ({downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB)", end='')
        
        print("\n✓ Download complete")
        
        # Extract
        print("Extracting...")
        result = subprocess.run(
            ["unzip", "-q", zip_file, "-d", version_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"✗ Extraction failed: {result.stderr}")
            return False
        
        # Move files from chrome-linux subfolder to version folder
        chrome_linux_path = os.path.join(version_path, "chrome-linux")
        if os.path.exists(chrome_linux_path):
            for item in os.listdir(chrome_linux_path):
                src = os.path.join(chrome_linux_path, item)
                dst = os.path.join(version_path, item)
                subprocess.run(["mv", src, dst], check=True)
            os.rmdir(chrome_linux_path)
        
        # Cleanup zip
        os.remove(zip_file)
        
        # Verify chrome binary exists
        chrome_binary = os.path.join(version_path, "chrome")
        if os.path.exists(chrome_binary):
            os.chmod(chrome_binary, 0o755)
            print(f"✓ Chrome binary found and made executable")
        else:
            print(f"⚠ Warning: Chrome binary not found at {chrome_binary}")
        
        print(f"✓ Successfully downloaded Chromium {version}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to download Chromium {version}: {e}")
        # Cleanup failed download
        if os.path.exists(version_path):
            subprocess.run(["rm", "-rf", version_path])
        return False

def main():
    print("\n" + "="*60)
    print("Chromium Multi-Version Downloader")
    print("="*60)
    
    os.makedirs(BASE_PATH, exist_ok=True)
    
    success_count = 0
    fail_count = 0
    
    for i, version in enumerate(CHROMIUM_VERSIONS, 1):
        print(f"\n[{i}/{len(CHROMIUM_VERSIONS)}] Processing {version}")
        if download_chromium(version):
            success_count += 1
        else:
            fail_count += 1
    
    print("\n" + "="*60)
    print("Download Summary")
    print("="*60)
    print(f"Total versions: {len(CHROMIUM_VERSIONS)}")
    print(f"✓ Successful: {success_count}")
    print(f"✗ Failed: {fail_count}")
    
    if os.path.exists(BASE_PATH):
        downloaded_versions = sorted(os.listdir(BASE_PATH))
        print(f"\nAvailable versions in {BASE_PATH}:")
        for v in downloaded_versions:
            size = subprocess.check_output(
                ["du", "-sh", os.path.join(BASE_PATH, v)]
            ).decode().split()[0]
            print(f"  - {v} ({size})")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
