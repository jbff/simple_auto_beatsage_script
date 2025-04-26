#!/usr/bin/env python

"""
Simple Auto BeatSage Script

This script automates the process of generating Beat Saber custom levels using BeatSage.com.
It can process multiple audio files in a directory and generate Beat Saber maps for each one.

Usage Examples:
    # Process all audio files in a directory
    python main.py /path/to/audio/files
    
    # Process files with custom settings
    python main.py --input /path/to/audio/files \
                  --output /path/to/output \
                  --difficulties Hard,Expert \
                  --modes Standard,90Degree \
                  --events DotBlocks,Obstacles \
                  --environment DefaultEnvironment \
                  --model_tag v2

Error Handling:
    The script handles various error conditions:
    - FileNotFoundError: When input directory doesn't exist
    - RuntimeError: When file processing fails
    - requests.exceptions.RequestException: Network-related errors
    - json.JSONDecodeError: Invalid API responses
    - Other unexpected errors during processing

    Error messages are printed to stderr and the script exits with code 1 on error.
"""

import argparse
import json
import os
import sys
import time
import math
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import zipfile

import browsercookie
import requests
from tinytag import TinyTag

# To process YouTube URLs from text file
import yt_dlp
import tempfile

# Check if terminal supports colors
use_colors = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

# Define color codes
GREEN = '\033[92m' if use_colors else ''
YELLOW = '\033[93m' if use_colors else ''
BLUE = '\033[94m' if use_colors else ''
CYAN = '\033[96m' if use_colors else ''
BOLD = '\033[1m' if use_colors else ''
RESET = '\033[0m' if use_colors else ''

# Define emojis
MUSIC = '🎵'
UPLOAD = '📤'
PROCESS = '⚙️'
DOWNLOAD = '📥'
EXTRACT = '📂'
CHECK = '✅'
DONE = '✨'
WARNING = '⚠️'
SKIP = '⏭️'
ERROR = '❌'
SUCCESS = '🎉'
LIGHT = '💡'

# API Configuration
base_url = 'https://beatsage.com'
create_url = base_url + "/beatsaber_custom_level_create"

# Headers for BeatSage API requests
headers_beatsage = {
    'authority': 'beatsage.com',
    'method': 'POST',
    'path': '/beatsaber_custom_level_create',
    'scheme': 'https',
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9',
    'origin': base_url,
    'pragma': 'no-cache',
    'referer': base_url,
    'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'x-kl-ajax-request': 'Ajax_Request'
}

class Note:
    def __init__(self, note: Dict[str, Any], next_note: Dict[str, Any] = None):
        self.raw = note
        self.padding = (next_note["_time"] if next_note else note["_time"] + 1) - note["_time"]

def calculate_laser_speed(padding: float) -> int:
    return math.ceil((math.ceil((2 / padding) + 1) ** 2) / 4)

def add_lighting_events(beatmap: Dict[str, Any]) -> Dict[str, Any]:
    last_padding = 0
    last_time = None
    left_laser_next = True
    pace_changes = []
    beatmap["_events"] = []

    for i in range(len(beatmap["_notes"])):
        # Find next note that isn't on the same beat
        next_note = None
        n = i
        added_ring_rotation = False
        double_lasers = False
        
        while next_note is None:
            n += 1
            if n >= len(beatmap["_notes"]):
                next_note = {"_time": beatmap["_notes"][n-1]["_time"] * 2}
                break
            
            next_up = beatmap["_notes"][n]
            if next_up["_time"] == beatmap["_notes"][i]["_time"]:
                if not added_ring_rotation:
                    beatmap["_events"].append({
                        "_time": beatmap["_notes"][i]["_time"],
                        "_type": 8,
                        "_value": 0
                    })
                    added_ring_rotation = True
                double_lasers = True
                continue
            next_note = next_up

        # Skip stacked events
        if last_time == beatmap["_notes"][i]["_time"]:
            continue

        note = Note(beatmap["_notes"][i], next_note)
        light_value = None
        light_type = None
        pace_prefix = None

        # Determine lighting effects based on note type and timing
        if note.raw["_cutDirection"] == 8 or note.raw["_type"] == 3:
            # Add back light effects for bombs or blocks cut in any direction
            beatmap["_events"].append({
                "_time": note.raw["_time"],
                "_type": 0,
                "_value": 6 if note.padding < 1 else 2
            })
            beatmap["_events"].append({
                "_time": note.raw["_time"],
                "_type": 4,
                "_value": 0
            })
            if note.raw["_type"] == 3:  # Skip if bomb
                continue
        elif note.padding >= 2:
            if last_padding < 2 or i < 1:
                beatmap["_events"].append({
                    "_time": note.raw["_time"],
                    "_type": 9,
                    "_value": 0
                })
                pace_prefix = "0"
            light_type = 4
            light_value = 3
        elif note.padding >= 1:
            if last_padding < 1 or last_padding >= 2 or i < 1:
                beatmap["_events"].append({
                    "_time": note.raw["_time"],
                    "_type": 9,
                    "_value": 0
                })
                pace_prefix = "a"
            light_type = 4
            light_value = 2
        else:
            if last_padding >= 1 or i < 1:
                beatmap["_events"].append({
                    "_time": note.raw["_time"],
                    "_type": 9,
                    "_value": 0
                })
                pace_prefix = "b"
            light_type = 4
            light_value = 6

        if pace_prefix is not None:
            pace_changes.append(f"{pace_prefix}{note.raw['_time']}")

        if note.raw["_cutDirection"] != 8:
            beatmap["_events"].append({
                "_time": note.raw["_time"],
                "_type": light_type,
                "_value": light_value
            })
            beatmap["_events"].append({
                "_time": note.raw["_time"],
                "_type": 0,
                "_value": 0
            })

        # Handle laser effects
        laser_color = 7 if note.padding < 1 else 3
        laser_side = None

        if double_lasers and note.padding >= 2:
            beatmap["_events"].append({
                "_time": note.raw["_time"],
                "_type": 3,
                "_value": laser_color
            })
            beatmap["_events"].append({
                "_time": note.raw["_time"],
                "_type": 2,
                "_value": laser_color
            })
            beatmap["_events"].append({
                "_time": note.raw["_time"],
                "_type": 12,
                "_value": calculate_laser_speed(note.padding)
            })
            beatmap["_events"].append({
                "_time": note.raw["_time"],
                "_type": 13,
                "_value": calculate_laser_speed(note.padding)
            })
        elif left_laser_next:
            left_laser_next = False
            laser_side = 2
            beatmap["_events"].append({
                "_time": note.raw["_time"],
                "_type": 3,
                "_value": 0
            })
        else:
            left_laser_next = True
            laser_side = 3
            beatmap["_events"].append({
                "_time": note.raw["_time"],
                "_type": 2,
                "_value": 0
            })

        if not double_lasers or note.padding < 2:
            beatmap["_events"].append({
                "_time": note.raw["_time"],
                "_type": 12 if laser_side == 2 else 13,
                "_value": calculate_laser_speed(note.padding)
            })
            beatmap["_events"].append({
                "_time": note.raw["_time"],
                "_type": laser_side,
                "_value": laser_color
            })

        last_padding = note.padding
        last_time = note.raw["_time"]

    # Add ring lights for paced sections
    for i in range(len(pace_changes)):
        ring_value = 0
        # Skip empty strings or strings without at least one character
        if not pace_changes[i] or len(pace_changes[i]) < 1:
            continue
            
        prefix = pace_changes[i][0]
        
        if prefix == "a":
            ring_value = 3
        elif prefix == "b":
            ring_value = 7
        
        if ring_value == 0 or i == len(pace_changes) - 1:
            continue

        # Safely parse the current timestamp
        try:
            current_timestamp = math.ceil(float(pace_changes[i][1:]))
            next_timestamp = math.ceil(float(pace_changes[i+1][1:]))
        except (ValueError, IndexError) as e:
            continue  # Skip this pace change if there's an error parsing timestamps
        # Get the original timestamp as float for precise comparison
        original_timestamp = float(pace_changes[i][1:])
        if math.ceil(original_timestamp) != original_timestamp:
            beatmap["_events"].append({
                "_time": original_timestamp,
                "_type": 1,
                "_value": ring_value
            })

        while current_timestamp < next_timestamp:
            beatmap["_events"].append({
                "_time": current_timestamp,
                "_type": 1,
                "_value": ring_value
            })
            current_timestamp += 1

    return beatmap

def create_light_map(filename: Union[str, Path]) -> None:
    """
    Add lighting events to a Beat Saber level file.
    
    Args:
        filename: Path to the level file (.dat)
        
    Raises:
        RuntimeError: If the file cannot be processed
    """
    try:
        # Read the beatmap file
        with open(filename, 'r') as f:
            beatmap = json.load(f)

        # Validate beatmap
        if "_version" not in beatmap:
            raise RuntimeError("Invalid beatmap version! V3 mapping is not supported yet!")
        if "_notes" not in beatmap:
            raise RuntimeError("Not a valid beatmap!")

        # Add lighting events
        beatmap = add_lighting_events(beatmap)

        # Write to a temporary file first
        temp_file = Path(filename).with_suffix('.dat.tmp')
        with open(temp_file, 'w') as f:
            json.dump(beatmap, f)

        # Replace the original file
        temp_file.replace(filename)
        
    except Exception as e:
        raise RuntimeError(f"Failed to add lighting to {filename}: {str(e)}")

def get_mp3_tag(file: Union[str, Path]) -> Tuple[str, str, bytes]:
    """
    Extract metadata from an audio file using TinyTag.
    
    Args:
        file: Path to the audio file
        
    Returns:
        Tuple containing:
        - title: Audio file title (empty string if not found)
        - artist: Audio file artist (empty string if not found)
        - cover_art: Cover art image data (empty bytes if not found)
        
    Raises:
        RuntimeError: If the file cannot be read or metadata cannot be extracted
    """
    try:
        tag = TinyTag.get(file, image=True)
        title = tag.title or ''
        artist = tag.artist or ''
        if not tag.images.any is None:
            cover = tag.images.any.data or b''
        else:
            cover = b''
        return title, artist, cover
    except Exception as e:
        raise RuntimeError(f"Failed to read MP3 tags from {file}: {str(e)}")

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be used as a filename.
    
    Args:
        filename: The string to sanitize
        
    Returns:
        A sanitized string safe for use as a filename
    """
    # Replace invalid characters with underscores
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    # Replace multiple spaces with single space
    filename = ' '.join(filename.split())
    return filename

def get_output_filename(file: Union[str, Path]) -> str:
    """
    Get the output filename based on ID3 tags.
    
    Args:
        file: Path to the audio file
        
    Returns:
        A sanitized filename in the format "Track - Artist"
    """
    title, artist, _ = get_mp3_tag(file)
    
    # If either tag is missing, use the original filename
    if not title or not artist:
        return Path(file).stem
    
    # Sanitize both title and artist
    title = sanitize_filename(title)
    artist = sanitize_filename(artist)
    
    return f"{title} - {artist}"

def get_map(file: Union[str, Path], outputdir: Union[str, Path], diff: str, modes: str, 
           events: str, env: str, tag: str) -> None:
    """
    Generate a Beat Saber map for an audio file using BeatSage.
    
    Args:
        file: Path to the audio file
        outputdir: Directory to save the generated map
        diff: Comma-separated difficulties to generate
        modes: Comma-separated game modes to generate
        events: Comma-separated event types to include
        env: Environment name for the map
        tag: Model version tag to use
        
    Raises:
        RuntimeError: If map generation fails for any reason
        requests.exceptions.RequestException: If network requests fail
        json.JSONDecodeError: If API responses are invalid
        
    The function will:
    1. Extract metadata from the audio file
    2. Upload the file to BeatSage
    3. Monitor the generation progress
    4. Download the generated map
    5. Save it to the output directory
    6. Add lighting events to all .dat files except Info.dat
    """
    try:
        audio_title, audio_artist, cover_art = get_mp3_tag(file)
        original_filename = Path(file).stem
        output_filename = get_output_filename(file)
        
        # If we're using the original filename, let the user know
        if output_filename == original_filename:
            print(f"{YELLOW}{WARNING} No valid ID3 tags found, using original filename: {BLUE}{original_filename}{RESET}")
        
        payload = {
            'audio_metadata_title': audio_title or original_filename,
            'audio_metadata_artist': audio_artist or 'Unknown Artist',
            'difficulties': diff,
            'modes': modes,
            'events': events,
            'environment': env,
            'system_tag': tag
        }

        files: Dict[str, Tuple[str, bytes, str]] = {
            "audio_file": ("audio_file", Path(file).read_bytes(), "audio/mpeg")
        }
        if cover_art:
            files["cover_art"] = ("cover_art", cover_art, "image/jpeg")

        # load cookies from all supported/findable browsers
        cj = browsercookie.load()
        session = requests.Session()
        session.cookies.update(cj)
        
        print(f"{YELLOW}{UPLOAD} Uploading audio file to BeatSage...{RESET}", end='', flush=True)
        response = session.post(create_url, headers=headers_beatsage, data=payload, files=files)
        print(f" {GREEN}{CHECK} DONE{RESET}")
        
        if response.status_code == 413:
            raise RuntimeError("File size or song length limit exceeded (32MB, 10min for non-Patreon supporters)")
            
        response.raise_for_status()
        
        map_id = json.loads(response.text)['id']
        heart_url = f"{base_url}/beatsaber_custom_level_heartbeat/{map_id}"
        download_url = f"{base_url}/beatsaber_custom_level_download/{map_id}"
        
        print(f"{YELLOW}{PROCESS} Generating map...{RESET}", end='', flush=True)
        max_attempts = 75  # 17.5 minutes maximum
        attempt = 0
        
        while attempt < max_attempts:
            heartbeat_response = session.get(heart_url, headers=headers_beatsage)
            heartbeat_response.raise_for_status()
            status_data = json.loads(heartbeat_response.text)
            status = status_data['status']
            
            if status == "DONE":
                print(f" {GREEN}{CHECK} DONE{RESET}")
                break
            elif status == "ERROR":
                raise RuntimeError("Map generation failed")

            # No progress info available
            print('.', end='', flush=True)
                    
            time.sleep(14)
            attempt += 1
        else:
            raise RuntimeError("Map generation timed out")
            
        print(f"{YELLOW}{DOWNLOAD} Downloading generated map...{RESET}", end='', flush=True)
        response = session.get(download_url, headers=headers_beatsage, stream=True)
        response.raise_for_status()
        
        # Get content length if available
        total_size = int(response.headers.get('content-length', 0))
        
        # Write the zip file first
        output_path = Path(outputdir) / f"{output_filename}.zip"
        
        if total_size > 0:
            with open(output_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
        else:
            # If content length is unknown, just save the file
            output_path.write_bytes(response.content)
            
        print(f" {GREEN}{CHECK} DONE{RESET}")
        
        # Create the extraction directory with the same basename
        extract_dir = Path(outputdir) / output_filename
        
        # Extract the zip file
        print(f"{YELLOW}{EXTRACT} Extracting map files...{RESET}", end='', flush=True)
        with zipfile.ZipFile(output_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        # Remove the original zip file if extraction was successful
        if extract_dir.exists():
            output_path.unlink()
            
        print(f" {GREEN}{CHECK} DONE{RESET}")
        
        # Process all .dat files except Info.dat
        print(f"{YELLOW}{LIGHT} Adding lighting events to levels...{RESET}", end='', flush=True)
        for dat_file in extract_dir.glob('*.dat'):
            if dat_file.name != 'Info.dat':
                try:
                    create_light_map(dat_file)
                except Exception as e:
                    print(f"\n{YELLOW}{WARNING} Failed to add lighting to {dat_file.name}: {str(e)}{RESET}")
                    continue
        print(f" {GREEN}{CHECK} DONE{RESET}")
        
        print(f"{GREEN}{MUSIC} Map generation complete, {BLUE}{output_filename}{RESET} saved in {CYAN}{extract_dir}{RESET} {DONE}")
        print(f"{BOLD}---------------------------{RESET}")
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network error occurred: {str(e)}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON response: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")

def get_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Namespace containing parsed arguments
        
    The function handles both full argument parsing and the special case
    where a single argument is provided (assumed to be the input path).
    """
    parser = argparse.ArgumentParser(description='Simple auto beatsage from local files or YouTube URLs by rote66')
    parser.add_argument('--input', '-i', type=Path, required=True,
                       help='Input path (directory of audio files, single audio file, or text file with YouTube URLs)')
    parser.add_argument('--output', '-o', type=Path, default=None,
                       help='Output folder for generated maps (defaults to input directory for directories, or input file directory for files)')
    parser.add_argument('--difficulties', '-d', type=str, default='Expert,ExpertPlus',
                       help='Comma-separated difficulties: Normal,Hard,Expert,ExpertPlus')
    parser.add_argument('--modes', '-m', type=str, default='Standard',
                       help='Comma-separated modes: Standard,90Degree,NoArrows,OneSaber')
    parser.add_argument('--events', '-e', type=str, default='DotBlocks,Obstacles',
                       help='Comma-separated events: DotBlocks,Obstacles,Bombs')
    parser.add_argument('--environment', '-env', type=str, default='FitBeatEnvironment',
                       help='Environment name: DefaultEnvironment, Origins, TriangleEnvironment, BigMirrorEnvironment, NiceEnvironment, KDAEnvironment, MonstercatEnvironment, DragonsEnvironment, CrabRaveEnvironment, PanicEnvironment, RocketEnvironment, GreenDayEnvironment, GreenDayGrenadeEnvironment, TimbalandEnvironment, FitBeatEnvironment, LinkinParkEnvironment, BTSEnvironment, KaleidoscopeEnvironment, InterscopeEnvironment, SkrillexEnvironment, BillieEnvironment, HalloweenEnvironment, GagaEnvironment')
    parser.add_argument('--model_tag', '-t', type=str, default='v2',
                       help='Model version: v1, v2, v2-flow')
    
    # Handle the case where a single argument is provided (assumed to be input path)
    if len(sys.argv) == 2 and Path(sys.argv[1]).exists():
        return parser.parse_args(['-i', sys.argv[1]])
    return parser.parse_args()

def process_files(args: argparse.Namespace) -> None:
    """
    Process input based on its type:
    - If directory: process all audio files in it
    - If audio file: process that single file
    - If text file: treat as list of YouTube URLs to download and process
    
    Args:
        args: Parsed command line arguments
        
    Raises:
        FileNotFoundError: If input doesn't exist
        RuntimeError: If processing fails for any file
    """
    if not args.input.exists():
        raise FileNotFoundError(f"Input does not exist: {args.input}")
        
    # Define supported audio extensions
    audio_extensions = {'.mp3','.aiff','.aac','.ogg','.wav','.flac'}
    
    # Handle output directory
    if args.output is None:
        if args.input.is_file():
            args.output = args.input.parent
        else:
            args.output = args.input
    else:
        args.output.mkdir(parents=True, exist_ok=True)
    
    # Handle different input types
    if args.input.is_dir():
        # Process all audio files in directory
        audio_files = [f for f in args.input.iterdir() 
                      if f.suffix.lower() in audio_extensions]
        
        if not audio_files:
            print(f"No audio files found in {args.input}")
            return
            
        total_files = len(audio_files)
        
        for idx, file in enumerate(audio_files, 1):
            process_single_file(file, args)
            
    elif args.input.suffix.lower() in audio_extensions:
        # Process single audio file
        process_single_file(args.input, args)
        
    elif args.input.suffix.lower() == '.txt':
        
        # Read URLs from text file
        with open(args.input, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
            
        if not urls:
            print(f"No URLs found in {args.input}")
            return
            
        total_files = len(urls)
        
        # Configure yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        for idx, url in enumerate(urls, 1):
            print(f"\n{BOLD}Processing URL {idx}/{total_files}: {BLUE}{url}{RESET}")
            try:
                # Create temporary directory for download
                with tempfile.TemporaryDirectory() as temp_dir:
                    ydl_opts['outtmpl'] = str(Path(temp_dir) / '%(title)s.%(ext)s')
                    
                    # Download audio
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        audio_file = Path(temp_dir) / f"{info['title']}.mp3"
                        
                        if not audio_file.exists():
                            raise RuntimeError("Failed to download audio file")
                            
                        # Process the downloaded file
                        process_single_file(audio_file, args)
                        
            except Exception as e:
                print(f"{YELLOW}{WARNING} Error processing {url}: {str(e)}{RESET}")
                continue
                
    else:
        raise RuntimeError(f"Unsupported input type: {args.input}")

def process_single_file(file: Path, args: argparse.Namespace) -> None:
    """
    Process a single audio file.
    
    Args:
        file: Path to the audio file
        args: Parsed command line arguments
    """
    output_filename = get_output_filename(file)
    output_zip = args.output / f"{output_filename}.zip"
    output_dir = args.output / output_filename
    
    if output_zip.exists() or output_dir.exists():
        print(f"{YELLOW}{SKIP} Skipping {file.name} - output already exists{RESET}")
        return
        
    print(f"\n{BOLD}Processing file: {BLUE}{file.name}{RESET}")
    try:
        get_map(file, args.output, args.difficulties, args.modes,
               args.events, args.environment, args.model_tag)
    except Exception as e:
        print(f"{YELLOW}{WARNING} Error processing {file.name}: {str(e)}{RESET}")
        return

if __name__ == '__main__':
    try:
        args = get_args()
        process_files(args)
        print(f"\n{GREEN}{SUCCESS} All files processed! {DONE}{RESET}")
    except Exception as e:
        print(f"{YELLOW}{ERROR} Error: {str(e)}{RESET}", file=sys.stderr)
        sys.exit(1)
