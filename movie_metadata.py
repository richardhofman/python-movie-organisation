#!/usr/local/bin/python3

''' Credit to github.com/oldo: https://gist.github.com/oldo/dc7ee7f28851922cca09 '''

import subprocess
import shlex
import json

# function to find the resolution of the input video file
def findVideoMetadata(pathToInputVideo):
    cmd = "ffprobe -v quiet -print_format json -show_streams"
    args = shlex.split(cmd)
    args.append(pathToInputVideo)
    # run the ffprobe process, decode stdout into utf-8 & convert to JSON
    ffprobeOutput = subprocess.check_output(args).decode('utf-8')
    ffprobeOutput = json.loads(ffprobeOutput)

    # Get relevant metadata
    video_stream = ffprobeOutput['streams'][0]
    audio_stream = ffprobeOutput['streams'][1]
    metadata = {}
    try:
        metadata['v_codec'] = video_stream['codec_name']
    except KeyError:
        metadata['v_codec'] = ''
        
    try:
        metadata['width'] = int(video_stream['width'])
    except KeyError:
        metadata['width'] = 0
    
    try:
        metadata['a_channels'] = int(audio_stream['channels'])
    except KeyError:
        metadata['a_channels'] = 0
    
    try:
        metadata['a_bitrate'] = float(audio_stream['bit_rate']) if 'bit_rate' in audio_stream.keys() else float(audio_stream['tags']['BPS'])
    except KeyError:
        metadata['a_bitrate'] = 0.0
        
    try:
        metadata['v_bitrate'] = float(video_stream['bit_rate']) if 'bit_rate' in video_stream.keys() else float(video_stream['tags']['BPS'])
    except KeyError:
        metadata['v_bitrate'] = 0.0
        
    return metadata

def videoQualityMetric(filename):
    try:
        md = findVideoMetadata(filename)
    except:
        return -100
    
    # Fudge some stuff and make a rough metric for relative quality...
    v_bitrate_mbs = md['v_bitrate'] / 1000000.0  # video bitrate in Mb/s
    a_bitrate_mbs = md['a_bitrate'] / 100000.0   # audio bitrate in 100* Kb/s
    channel_count_ratio = md['a_channels'] / 2.0 # num. channels.
    if md['v_codec'].lower() == 'h264':
        codec_awesomeness = 1
    elif md['v_codec'].lower() == 'hevc':
        codec_awesomeness = 2
    else:
        codec_awesomeness = 0
    if md['width'] > 1800:
        width_awesomeness = 1
    elif md['width'] < 1200:
        width_awesomeness = -1
    else:
        width_awesomeness = 0
    return v_bitrate_mbs + a_bitrate_mbs + channel_count_ratio + 3 * codec_awesomeness + 2 * width_awesomeness
    