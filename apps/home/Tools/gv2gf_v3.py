# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Author: hq@trekview.org
# Created: 2020-06-04
# Copyright: Trek View
# Licence: GNU AGPLv3
# -------------------------------------------------------------------------------

import os
import argparse
import pandas as pd
import datetime
from pathlib import Path
import subprocess
import sys
import json
import re
import traceback
import gpxpy
import logging

logging.basicConfig(level=logging.DEBUG)


def run_command(*args):
    try:
        out = subprocess.Popen(list(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        return stdout.decode('utf8')
    except:
        print(traceback.format_exc())
        return ''


def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes) / 60 + float(seconds) / (60 * 60)
    if direction == 'E' or direction == 'N':
        dd *= -1
    return dd


def dd2dms(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    return [d, m, sd]


def parse_dms(dms):
    """
    Parse degrees from dms string.
    """

    parts = re.split('[deg\'"]+', dms)
    lat = dms2dd(parts[0], parts[1], parts[2], parts[3])

    return lat


def get_seconds(time_str):
    """
    Parse time string to seconds
    ex: "00:01:20" -> 50, "20 s" -> 20
    """
    sec_group = re.search(r'(\d+\.?\d*) s', time_str)
    if sec_group:
        res = float(sec_group.group(1))
    else:
        secs = time_str.split(':')
        res = int(secs[0]) * 3600 + int(secs[1]) * 60 + int(secs[2])
    return res


def get_altitude_meters(altitude_str):
    m_group = re.search(r'(\d+\.?\d*)', altitude_str)
    if m_group:
        return float(m_group.group(1))
    return 0.0


def get_video_info(exiftool_executable, input_path):
    """
    Get Video Meta data and detail geo data
    """
    try:
        print("Fetching metadata from video...")
        video_info_text = run_command(
            exiftool_executable, '-j', '-ee', '-G3', '-s', '-api', 'largefilesupport=1', input_path)
        video_info = json.loads(video_info_text)[0]
        print(video_info)
    except:
        return None, None

    required_values = ['GPSLatitude', 'GPSLongitude', 'GPSAltitude', 'SampleTime', 'GPSDateTime']
    available_keys = re.findall(r'(Doc\d+):GPSLatitude', video_info_text)
    minified_video_info = {
        key: val
        for key, val in video_info.items()
        if not key.startswith('Doc')
    }
    data_list = []

    for k in available_keys:
        item = {}
        try:
            for s_k in required_values:
                key = '{}:{}'.format(k, s_k)
                val = video_info.get(key, None)
                if s_k == 'GPSDateTime':
                    date_format = '%Y:%m:%d %H:%M:%S.%f'
                    if 'Z' in val:
                        date_format = '{0}Z'.format(date_format)
                    item[s_k] = datetime.datetime.strptime(val, date_format)
                elif s_k == 'SampleTime':
                    item[s_k] = get_seconds(val)
                elif s_k in ['GPSLatitude', 'GPSLongitude']:
                    item[s_k] = parse_dms(val)
                else:
                    if val:
                        item[s_k] = get_altitude_meters(val)
                    else:
                        item[s_k] = None

            data_list.append(item)
        except:
            continue

    df_frames = pd.DataFrame(data_list)
    if not df_frames.empty:
        df_frames.sort_values('SampleTime', inplace=True)
        df_frames.drop_duplicates(subset='SampleTime', inplace=True)

    return minified_video_info, df_frames


def split_video_img(ffmpeg_executable, input_path, output_path, start_secs):
    res = run_command(ffmpeg_executable, '-ss', str(start_secs), '-i', input_path, '-frames:v', '1', output_path)
    return res


def update_splited_video_geo(exiftool_executable, file_path, start_time, start_secs, frame_start, frame_end, video_info):
    geo_data = {'GPSLatitude': None, 'GPSLongitude': None, 'GPSAltitude': None, 'GPSDateTime': None}
    if frame_start and frame_end:
        frame_start_time = frame_start.get('SampleTime') if frame_start else None
        frame_end_time = frame_end.get('SampleTime') if frame_end else None
        calculate_keys = ['GPSLatitude', 'GPSLongitude', 'GPSAltitude']
        start_diff = start_secs - frame_start_time
        end_diff = frame_end_time - start_secs
        geo_data = {
            k: frame_start.get(k, None) + (frame_end.get(k, None) - frame_start.get(k, None)) * start_diff / (start_diff + end_diff)
            for k in calculate_keys
        }
    elif frame_start:
        geo_data = frame_start
    elif frame_end:
        geo_data = frame_end

    geo_data['GPSDateTime'] = start_time + datetime.timedelta(0, start_secs)

    res = run_command(
        exiftool_executable,
        '-DateTimeOriginal={0}'.format(start_time.strftime("%Y:%m:%d %H:%M:%S")),
        '-GPSDateStamp={0}'.format(start_time.strftime("%Y:%m:%d")),
        '-GPSTimeStamp={}'.format(start_time.strftime("%H:%M:%S")),
        '-GPSLatitude={}'.format(geo_data.get('GPSLatitude')),
        '-GPSLongitude={}'.format(geo_data.get('GPSLongitude')),
        '-GPSAltitude={}'.format(geo_data.get('GPSAltitude')),
        '-ProjectionType={}'.format(video_info.get('Main:ProjectionType')),
        '-Make={}'.format(video_info.get('Main:Make'), ''),
        '-Model={}'.format(video_info.get('Main:Model'), ''),
        '-ImageWidth={}'.format(video_info.get('Main:ImageWidth')),
        '-ImageHeight={}'.format(video_info.get('Main:ImageHeight')),
        '-ImageSize={}'.format(video_info.get('Main:ImageSize')),
        '-UsePanoramaViewer=true',
        '-CroppedAreaImageHeightPixels={}'.format(video_info.get('Main:ImageHeight')),
        '-CroppedAreaImageWidthPixels={}'.format(video_info.get('Main:ImageWidth')),
        '-CroppedAreaImageWidthPixels={}'.format(video_info.get('Main:ImageWidth')),
        '-FullPanoHeightPixels={}'.format(video_info.get('Main:ImageHeight')),
        '-FullPanoWidthPixels={}'.format(video_info.get('Main:ImageWidth')),
        '-overwrite_original',
        file_path
    )
    return res, geo_data


def get_dict_from_frame(frame, idx):
    if len(frame.index) > 0:
        selected_frame = frame.iloc[idx]
        return {
            'GPSDateTime': selected_frame.get('GPSDateTime'),
            'GPSLatitude': selected_frame.get('GPSLatitude'),
            'GPSLongitude': selected_frame.get('GPSLongitude'),
            'SampleTime': selected_frame.get('SampleTime'),
            'GPSAltitude': selected_frame.get('GPSAltitude')
        }
    return None


def write_gpx_file(track_logs):
    print('Writing gpx log to log.gpx')
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    for log in track_logs:
        point = gpxpy.gpx.GPXTrackPoint(
            longitude=log.get('GPSLongitude'),
            latitude=log.get('GPSLatitude'),
            time=log.get('GPSDateTime')
        )
        gpx_segment.points.append(point)

    with open('log.gpx', 'w') as f:
        f.write(gpx.to_xml())


def set_csv_row(output_path, geo_data):
    item = {}
    path_list = output_path.split("\\")
    item['file_name'] = path_list[-1]
    item['lon'] = geo_data['GPSLongitude']
    item['lat'] = geo_data['GPSLatitude']
    return item


def geovideo_to_geoframes(exiftool_executable, ffmpeg_executable, video_info, df_frames, input_path, output_directory, frame_rates, time_mode):
    duration_secs = get_seconds(video_info.get('Main:MediaDuration'))
    start_secs = 0
    period_start = None
    period_end = None
    time_key = 'SampleTime'
    track_logs = []
    csv_logs = []

    output_directory = output_directory 
    if not os.path.isdir(os.path.abspath(output_directory)):
        os.mkdir(output_directory)

    if not df_frames.empty:
        start_time = df_frames['GPSDateTime'].iloc[0] if time_mode == 'timegps' else datetime.datetime.strptime(video_info.get('Main:CreateDate'), '%Y:%m:%d %H:%M:%S')
    else:
        start_time = datetime.datetime.strptime(video_info.get('Main:CreateDate'), '%Y:%m:%d %H:%M:%S')

    while True:
        output_path = os.path.join(output_directory, '{}.jpg'.format((start_time + datetime.timedelta(0, start_secs)).strftime('%Y_%m_%d_%H%M%S')))
        ffmpeg_res = split_video_img(ffmpeg_executable, input_path, output_path, start_secs)
        print('Got image from video at {} seconds. Path to file is {}'.format(start_secs, output_path))

        if not df_frames.empty:
            start_frame = df_frames[df_frames[time_key] <= start_secs]
            if start_frame.empty:
                period_start = None
            else:
                period_start = get_dict_from_frame(start_frame, len(start_frame.index) - 1)

            end_frame = df_frames[df_frames[time_key] > start_secs]
            if end_frame.empty:
                period_end = None
            else:
                period_end = get_dict_from_frame(end_frame, 0)

            print('Start to set the metadata of {}'.format(output_path))
            exif_res, geo_data = update_splited_video_geo(exiftool_executable, output_path, start_time, start_secs, period_start, period_end, video_info)
            
            track_logs.append(geo_data)
            csv_row = set_csv_row(output_path, geo_data)
            csv_logs.append(csv_row)
            print('End to set the metadata of {}'.format(output_path))

        start_secs += frame_rates

        if start_secs > duration_secs:
            break

    if track_logs:
        write_gpx_file(track_logs)

    df = pd.DataFrame(csv_logs)
    path_list = output_path.split("\\")
    file_name = path_list[-3] + ".csv"
    csv_file_name = "\\".join(path_list[0:len(path_list) - 2]) + "\\" + file_name
    df.to_csv(csv_file_name, index=False)

    return df, track_logs


def main_process(args):
    path = Path(__file__)
    time_mode = args.time.lower()
    frame_rate = 0

    if time_mode not in ['timegps', 'timecapture']:
        logging.error("Time mode should be one of 'timegps' or 'timecapture'.")
        return

    try:
        frame_rate = 1 / float(args.frame_rate)
        if frame_rate < 1:
            logging.error("Frame Rate should be less than 1.")
            return
    except Exception as e:
        logging.error(f"Frame Rate error: {str(e)}")
        return

    input_path = os.path.abspath(args.input_path)
    if not os.path.isfile(input_path):
        logging.error(f"{input_path} file does not exist.")
        return

    is_win_shell = True
    exiftool_executable = 'exiftool'

    if args.exif_path == 'No path specified':
        if 'win' in sys.platform and not 'darwin' in sys.platform:
            if os.path.isfile(os.path.join(path.parent.resolve(), 'exiftool.exe')):
                exiftool_executable = os.path.join(path.parent.resolve(), 'exiftool.exe')
            else:
                logging.error("""Executing this script on Windows requires either the "-e" option or store the exiftool.exe file in the working directory.""")
                return
        else:
            is_win_shell = False
    else:
        exiftool_executable = args.exif_path

    ffmpeg_executable = 'ffmpeg'
    if args.ffmpeg_path == 'No path specified':
        if 'win' in sys.platform and not 'darwin' in sys.platform:
            if os.path.isfile(os.path.join(path.parent.resolve(), 'ffmpeg.exe')):
                ffmpeg_executable = os.path.join(path.parent.resolve(), 'ffmpeg.exe')
            else:
                logging.error("""Executing this script on Windows requires either the "-e" option or store the ffmpeg.exe file in the working directory.""")
                return
        else:
            is_win_shell = False
    else:
        ffmpeg_executable = args.ffmpeg_path

    output_path = os.path.abspath(args.output_directory)
    if not os.path.isdir(os.path.abspath(output_path)):
        os.mkdir(output_path)

    try:
        video_info, df_frames = get_video_info(exiftool_executable, input_path)
        if not video_info:
            logging.error("Video format is incorrect.")
            return

        if df_frames.empty:
            logging.warning("No GPS info!")
            return

        df, track_logs = geovideo_to_geoframes(exiftool_executable, ffmpeg_executable, video_info, df_frames, input_path, output_path, frame_rate, time_mode)

        # Print the DataFrame and track logs as JSON
        output = {
            'df': df.to_json(orient='records', date_format='iso'),
            'track_logs': track_logs
        }
        print(json.dumps(output))


    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Geovideo to Geoframes')

    parser.add_argument('-e', '--exiftool-exec-path', action='store', default='No path specified', dest='exif_path', help='Optional: path to Exiftool executable.')

    parser.add_argument('-f', '--ffmpeg-exec-path', action='store', default='No path specified', dest='ffmpeg_path', help='Optional: path to ffmpeg executable.')

    parser.add_argument('-t', '--time', action='store', default='timegps', help='"timegps" or "timecapture"')

    parser.add_argument('input_path', action='store', help='Path to input video.')

    parser.add_argument('-r', '--frame-rate', action='store', help='Frame rates it should be less than 1')

    parser.add_argument('output_directory', action="store", help='Path to output folder.')

    input_args = parser.parse_args()
    main_process(input_args)
