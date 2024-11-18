#!/usr/bin/env python

import os
import subprocess

MONGO_URI = "mongodb://localhost:27017/FYP"
BACKUP_DIR = "mongo_backups"

def get_latest_backup_path():
    # List all directories in the backup directory
    backups = [d for d in os.listdir(BACKUP_DIR) if os.path.isdir(os.path.join(BACKUP_DIR, d))]
    
    if not backups:
        print("No backups found.")
        return None
    
    # Sort directories by name (assuming the name contains the timestamp)
    backups.sort(reverse=True)
    
    # Return the latest backup path
    return os.path.join(BACKUP_DIR, backups[0])

def restore_mongo(backup_path):
    # Check if backup path exists
    if not os.path.exists(backup_path):
        print(f"Backup path does not exist: {backup_path}")
        return

    # Run mongorestore command
    try:
        backup_path = os.path.join(backup_path, "FYP")
        subprocess.run(["A_QGIS\Tools\mongorestore.exe", "--uri", MONGO_URI, "--drop", backup_path], check=True)
        print(f"Restore successful from: {backup_path}")
    except subprocess.CalledProcessError as e:
        print(f"Restore failed: {e}")

if __name__ == "__main__":
    backup_path = get_latest_backup_path()
    if backup_path:
        restore_mongo(backup_path)