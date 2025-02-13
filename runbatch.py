import subprocess
import os

# Get the current working directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the relative path to the batch file
batch_file_path = os.path.join(current_dir, 'run.bat')

# Run the batch file
subprocess.run([batch_file_path])