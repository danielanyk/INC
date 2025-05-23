#!/usr/bin/env python

import os
import subprocess

MONGO_URI = "mongodb://localhost:27017/newdb"
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
    if not os.path.exists(backup_path):
        print(f"Backup path does not exist: {backup_path}")
        return False

    backup_path = os.path.join(backup_path, "newdb")

    try:
        completed_process = subprocess.run(
            ["A_QGIS\\Tools\\mongorestore.exe", "--uri", MONGO_URI, "--drop", backup_path],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"Restore successful from: {backup_path}")
        print("Output:", completed_process.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Restore failed: {e}")
        print("stderr:", e.stderr)
        return False

if __name__ == "__main__":
    backup_path = get_latest_backup_path()
    if backup_path:
        success = restore_mongo(backup_path)
        if not success:
            exit(1)  # Non-zero exit code for failure
    else:
        print("No backup found")
        exit(1)