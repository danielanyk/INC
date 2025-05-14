# import os
# import datetime
# import subprocess
# import sys

# def get_video_duration(ffmpeg_path, video_path):
#     """Get video duration in seconds using ffmpeg."""
#     result = subprocess.run(
#         [ffmpeg_path, "-i", video_path],
#         stderr=subprocess.PIPE,
#         stdout=subprocess.PIPE,
#         text=True
#     )

#     for line in result.stderr.splitlines():
#         if "Duration" in line:
#             duration_str = line.split("Duration:")[1].split(",")[0].strip()
#             h, m, s = duration_str.split(':')
#             return int(h) * 3600 + int(m) * 60 + float(s)
#     return 0

# def split_video_img(ffmpeg_executable, input_path, output_path, start_secs):
#     """Use FFmpeg to extract a frame at the given time (in seconds)."""
#     cmd = [
#         ffmpeg_executable,
#         '-ss', str(start_secs),
#         '-i', input_path,
#         '-frames:v', '1',
#         '-q:v', '2',
#         output_path
#     ]
#     result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#     return result

# def extract_frames(ffmpeg_executable, video_path, output_directory, frame_rate):
#     duration_secs = get_video_duration(ffmpeg_executable, video_path)
#     start_secs = 0

#     os.makedirs(output_directory, exist_ok=True)
#     extracted = 0

#     while start_secs <= duration_secs:
#         output_filename = f"{int(start_secs):05d}.jpg"
#         output_path = os.path.join(output_directory, output_filename)

#         result = split_video_img(ffmpeg_executable, video_path, output_path, start_secs)
#         if result.returncode != 0:
#             print(f"Failed at {start_secs:.2f}s:\n{result.stderr}", file=sys.stderr)
#         else:
#             print(f"Extracted frame at {start_secs:.2f}s to {output_path}")
#             extracted += 1
#         start_secs += frame_rate

#     if extracted == 0:
#         print("No frames extracted.", file=sys.stderr)
#     else:
#         print(f"Successfully extracted {extracted} frames.")

# if __name__ == "__main__":
#     if len(sys.argv) != 7:
#         print("Usage: python gv2f.py -f <ffmpeg_path> -r <rate> <video_path> <output_dir>")
#         sys.exit(1)

#     ffmpeg_path = sys.argv[2]
#     frame_rate = float(sys.argv[4])
#     video_path = sys.argv[5]
#     output_dir = sys.argv[6]

#     extract_frames(ffmpeg_path, video_path, output_dir, frame_rate)

import os
import subprocess
import sys
import exiftool
import json
import traceback
import datetime

BASE_DIR = os.path.dirname(__file__)
EXIFTOOL_BINARY = os.path.join(BASE_DIR,"exiftool.exe")
def get_video_duration(ffmpeg_path, video_path):
    """Get video duration in seconds using ffmpeg."""
    result = subprocess.run(
        [ffmpeg_path, "-i", video_path],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    for line in result.stderr.splitlines():
        if "Duration" in line:
            duration_str = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = duration_str.split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0


def run_command(*args):
    """
    Executes a command and returns the output as a string.
    Uses subprocess.Popen for better control over process execution.
    """
    try:
        out = subprocess.Popen(list(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        return stdout.decode('utf8')
    except Exception as e:
        print(f"Error occurred: {e}")
        print(traceback.format_exc())
        return ''

def parse_dms(dms_str):
    """
    Converts GPS DMS (Degrees, Minutes, Seconds) with N/S/E/W to decimal degrees.
    Example input: '1 deg 20\' 25.34" N'
    """
    dms_str = dms_str.replace("deg", "").replace("'", "").replace('"', "")
    dms_str = dms_str.strip()

    # Extract direction and remove it from string
    direction = None
    if dms_str.endswith(("N", "S", "E", "W")):
        direction = dms_str[-1]
        dms_str = dms_str[:-1].strip()

    # Now split by whitespace (multiple spaces handled)
    parts = dms_str.split()
    if len(parts) != 3:
        print(f"Invalid DMS format: {dms_str}")
        return None

    try:
        degrees = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
    except ValueError:
        print(f"Invalid number in DMS: {parts}")
        return None

    decimal = degrees + minutes / 60 + seconds / 3600

    # Apply negative sign for S or W
    if direction in ('S', 'W'):
        decimal = -decimal

    return decimal

def extract_video_metadata(video_path, exiftool_path=EXIFTOOL_BINARY):
    """
    Extract GPS and timestamp metadata from the video using exiftool.
    Uses the run_command function to get JSON output.
    """
    # Run exiftool command and capture JSON output
    raw_json = run_command(
        exiftool_path,
        '-j',  # Output in JSON format
        '-ee',  # Extract all information
        '-G3',  # Group tags
        '-s',  # Short output (no tag names)
        '-api', 'largefilesupport=1',  # Handle large files
        video_path
    )

    if not raw_json:
        return None, None, None

    try:
        metadata_list = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None, None, None

    if not metadata_list:
        return None, None, None

    meta = metadata_list[0]
    print("Metadata:", metadata_list)

    # Extracting GPS coordinates (if available)
    lat_str = meta.get("Doc1:GPSLatitude")
    lon_str = meta.get("Doc1:GPSLongitude")

    # If GPS data is available, convert it from DMS to decimal degrees
    if lat_str and lon_str:
        lat = parse_dms(lat_str)
        lon = parse_dms(lon_str)
    else:
        lat = lon = None

    # Extracting timestamp (with fallbacks)
    timestamp = (
        meta.get("QuickTime:CreateDate")  # Video create date
        or meta.get("EXIF:DateTimeOriginal")  # EXIF timestamp
        or meta.get("TrackCreateDate")  # Track create date
        or meta.get("MediaCreateDate")  # Media creation date
    )

    # If timestamp is in ISO format with 'Z' at the end, remove 'Z'
    if isinstance(timestamp, str) and timestamp.endswith("Z"):
        timestamp = timestamp[:-1]

    # Convert timestamp to datetime object if necessary
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.datetime.strptime(timestamp, "%Y:%m:%d %H:%M:%S")
        except ValueError:
            # Handle any timestamp format issues
            print(f"Warning: Unable to parse timestamp {timestamp}")
            timestamp = None
    print(f"Latitude: {lat}, Longitude: {lon}, Timestamp: {timestamp}")
    return lat, lon, timestamp

def split_video_img(ffmpeg_executable, input_path, output_path, start_secs):
    """Use FFmpeg to extract a single frame at the given time."""
    cmd = [ffmpeg_executable, '-ss', str(start_secs), '-i', input_path, '-frames:v', '1', '-q:v', '2', output_path]
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def extract_frames_with_metadata(ffmpeg_executable, video_path, output_directory, frame_rate=1):
    """
    Extract frames at a given rate and prepend each record with video metadata.
    Returns a tuple: (metadata, list_of_frame_paths)
    """
    # 1. Video metadata
    lat, lon, timestamp = extract_video_metadata(video_path)
    DEFAULT_LAT, DEFAULT_LON = 1.3521, 103.8198
    if lat is None and lon is None:
        lat, lon = DEFAULT_LAT, DEFAULT_LON
    if not timestamp:
        timestamp = "Unknown"

    # 2. Extract frames
    duration = get_video_duration(ffmpeg_executable, video_path)
    os.makedirs(output_directory, exist_ok=True)
    frames = []
    t = 0.0
    while t <= duration:
        fname = f"{int(t):05d}.jpg"
        out_path = os.path.join(output_directory, fname)
        res = split_video_img(ffmpeg_executable, video_path, out_path, t)
        if res.returncode == 0:
            frames.append(out_path)
        else:
            print(f"Frame extraction failed at {t}s: {res.stderr}", file=sys.stderr)
        t += frame_rate

    return {'latitude': lat, 'longitude': lon, 'timestamp': timestamp}, frames


if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Usage: python gv2f.py -f <ffmpeg_path> -r <rate> <video_path> <output_dir>")
        sys.exit(1)
    ffmpeg_path = sys.argv[2]
    frame_rate = float(sys.argv[4])
    video_path = sys.argv[5]
    output_dir = sys.argv[6]

    meta, frame_list = extract_frames_with_metadata(ffmpeg_path, video_path, output_dir, frame_rate)
    print("Video Metadata:", meta)
    print("Extracted frames:", frame_list)