#!/usr/bin/env python

import os
import subprocess
from datetime import datetime

MONGO_URI = "mongodb://localhost:27017/newdb"
BACKUP_DIR = "mongo_backups"

def backup_mongo():
    # Create backup directory if it doesn't exist
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    # Generate backup file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}")

    # Run mongodump command
    try:
        subprocess.run(["A_QGIS\Tools\mongodump.exe", "--uri", MONGO_URI, "--out", backup_path], check=True)
        print(f"Backup successful: {backup_path}")
    except subprocess.CalledProcessError as e:
        print(f"Backup failed: {e}")

if __name__ == "__main__":
    backup_mongo()