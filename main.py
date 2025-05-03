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
                  --environment default \
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
import shutil

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

# Option mappings
environments = {
    'default': 'DefaultEnvironment',
    'origins': 'Origins',
    'triangle': 'TriangleEnvironment',
    'nice': 'NiceEnvironment',
    'bigmirror': 'BigMirrorEnvironment',
    'dragons': 'DragonsEnvironment',
    'kda': 'KDAEnvironment',
    'monstercat': 'MonstercatEnvironment',
    'crabrave': 'CrabRaveEnvironment',
    'panic': 'PanicEnvironment',
    'rocket': 'RocketEnvironment',
    'greenday': 'GreenDayEnvironment',
    'greendaygrenade': 'GreenDayGrenadeEnvironment',
    'timbaland': 'TimbalandEnvironment',
    'fitbeat': 'FitBeatEnvironment',
    'linkinpark': 'LinkinParkEnvironment',
}

difficulties = {
    'normal': 'Normal',
    'norm': 'Normal',
    'hard': 'Hard',
    'expert': 'Expert',
    'exp': 'Expert',
    'expertplus': 'ExpertPlus',
    'explus': 'ExpertPlus',
}

modes = {
    'standard': 'Standard',
    'std': 'Standard',
    '90degree': '90Degree',
    '90deg': '90Degree',
    'noarrows': 'NoArrows',
    'onesaber': 'OneSaber',
}

events = {
    'dotblocks': 'DotBlocks',
    'dots': 'DotBlocks',
    'obstacles': 'Obstacles',
    'obs': 'Obstacles',
    'bombs': 'Bombs',
}

model_tags = {
    'one': 'v1',
    'v1': 'v1',
    'two': 'v2',
    'v2': 'v2',
    'flow': 'v2-flow',
}

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

def check_beatsage_cookie(cj: browsercookie.cookielib.CookieJar) -> Tuple[bool, Optional[str]]:
    """
    Check if there is a valid BeatSage session cookie.
    
    Args:
        cj: CookieJar from browsercookie
        
    Returns:
        Tuple containing:
        - bool: True if valid cookie found, False otherwise
        - Optional[str]: Expiry message if cookie found
    """
    try:
        session_cookie = cj._cookies['beatsage.com']['/']['session']
        expiry = session_cookie.expires
        if expiry is None:
            return True, "Session cookie found (no expiry)"
            
        cookie_expired = time.time() >= expiry
        if cookie_expired:
            return False, f"Session cookie expired on {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expiry))}"
        else:
            return True, f"Session cookie valid until {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expiry))}"
    except (KeyError, AttributeError):
        return False, "No session cookie found"

def get_map(file: Union[str, Path], outputdir: Union[str, Path], diff: str, modes: str, 
           events: str, env: str, tag: str, use_patreon: bool = False) -> None:
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
        use_patreon: Whether to require a valid BeatSage cookie
        
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
        
        # Check for valid BeatSage session cookie
        has_valid_cookie, cookie_message = check_beatsage_cookie(cj)
        if has_valid_cookie:
            print(f"{GREEN}{CHECK} {cookie_message} - Patreon features should be available{RESET}")
        else:
            if use_patreon:
                print(f"{YELLOW}{WARNING} {cookie_message} - Patreon features required but not available{RESET}")
                print(f"{YELLOW}{WARNING} Please log in to BeatSage in your browser and try again{RESET}")
                sys.exit(1)
            else:
                print(f"{YELLOW}{WARNING} {cookie_message} - Patreon features may not be available{RESET}")
                print(f"{YELLOW}{WARNING} File size limit: 32MB, Song duration limit: 10 minutes{RESET}")
            
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

def get_option_help(options: Dict[str, str]) -> str:
    """
    Generate help text for an option dictionary.
    
    Args:
        options: Dictionary mapping aliases to values
        
    Returns:
        Formatted help text showing all valid options and their aliases
    """

    # Group aliases by their values
    value_groups = {}
    for alias, value in options.items():
        if value not in value_groups:
            value_groups[value] = []
        value_groups[value].append(alias)

    # Format each group
    groups = []
    for value, aliases in value_groups.items():
        # Sort aliases by length (longest first) and alphabetically
        aliases.sort(key=lambda x: (-len(x), x))
        # Format as "alias1 [alias2, alias3, ...]"
        primary = aliases[0]
        secondary = aliases[1:] if len(aliases) > 1 else []
        if secondary:
            groups.append(f"{primary} [{', '.join(secondary)}]")
        else:
            groups.append(primary)

    return ', '.join(groups)

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
    parser.add_argument('--difficulties', '-d', type=str, default='expert,expertplus',
                       help=f'Comma-separated difficulties: {get_option_help(difficulties)} (default: expert,expertplus)')
    parser.add_argument('--modes', '-m', type=str, default='standard',
                       help=f'Comma-separated modes: {get_option_help(modes)} (default: standard)')
    parser.add_argument('--events', '-e', type=str, default='dotblocks,obstacles',
                       help=f'Comma-separated events: {get_option_help(events)} (default: dotblocks,obstacles)')
    parser.add_argument('--environment', '-env', type=str, default='default',
                       help=f'Environment name: {get_option_help(environments)} (default: default)')
    parser.add_argument('--model_tag', '-t', type=str, default='two',
                       help=f'Model version: {get_option_help(model_tags)} (default: two)')
    parser.add_argument('--use-patreon', '-P', action='store_true',
                       help='Require valid BeatSage cookie for Patreon features (script will exit if no valid cookie found)')
    
    # Handle the case where a single argument is provided (assumed to be input path)
    if len(sys.argv) == 2 and Path(sys.argv[1]).exists():
        return parser.parse_args(['-i', sys.argv[1]])
    
    # Parse arguments and convert option values to lowercase
    args = parser.parse_args()
    args.difficulties = args.difficulties.lower()
    args.modes = args.modes.lower()
    args.events = args.events.lower()
    args.environment = args.environment.lower()
    args.model_tag = args.model_tag.lower()
    return args

def prepare_input_files(input_path: Path) -> Tuple[List[Path], Path]:
    """
    Prepare input files based on input type.
    
    Args:
        input_path: Path to input (directory, file, or text file with YouTube URLs)
        
    Returns:
        List of audio files to process
        
    Raises:
        FileNotFoundError: If input doesn't exist
        RuntimeError: If input type is unsupported or no valid files found
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input does not exist: {input_path}")
        
    # Define supported audio extensions
    audio_extensions = {'.mp3','.aiff','.aac','.ogg','.wav','.flac'}
    
   # Handle different input types
    if input_path.is_dir():
        # Process all audio files in directory
        audio_files = [f for f in input_path.iterdir() 
                      if f.suffix.lower() in audio_extensions]
        
        if not audio_files:
            raise RuntimeError(f"No audio files found in {input_path}")
            
    elif input_path.suffix.lower() in audio_extensions:
        # Process single audio file
        audio_files = [input_path]
        
    elif input_path.suffix.lower() == '.txt':
        # Read URLs from text file
        with open(input_path, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
            
        if not urls:
            raise RuntimeError(f"No URLs found in {input_path}")
            
        # Configure yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [lambda d: print(f"\r{YELLOW}{DOWNLOAD} Downloading: {d.get('_percent_str', '?')} {d.get('_speed_str', '')} {d.get('_eta_str', '')}{RESET}", end='', flush=True)],
            'quiet': True,
            'no_warnings': True,
        }
        
        # Create temporary directory for downloads
        temp_dir = tempfile.mkdtemp()
        audio_files = []
        
        try:
            for url in urls:
                try:
                    ydl_opts['outtmpl'] = str(Path(temp_dir) / '%(title)s.%(ext)s')
                    
                    # Download audio
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        audio_file = Path(temp_dir) / f"{info['title']}.mp3"
                        
                        if not audio_file.exists():
                            raise RuntimeError(f"Failed to download audio file from {url}")
                            
                        audio_files.append(audio_file)
                        print(f"\n{GREEN}{CHECK} Downloaded: {info['title']}{RESET}")
                        
                except Exception as e:
                    print(f"\n{YELLOW}{WARNING} Error downloading {url}: {str(e)}{RESET}")
                    continue
                    
            if not audio_files:
                raise RuntimeError("No audio files were successfully downloaded")
                
        except Exception as e:
            # Clean up temp directory on error
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise e
            
    else:
        raise RuntimeError(f"Unsupported input type: {input_path}")
        
    return audio_files

def validate_args(args: argparse.Namespace) -> None:
    """
    Validate command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Raises:
        ValueError: If any argument is invalid
    """
    # Validate environment
    if args.environment not in environments:
        raise ValueError(f"Invalid environment: {args.environment}. Must be one of: {get_option_help(environments)}")
        
    # Validate difficulties
    diffs = set(d.strip().lower() for d in args.difficulties.split(','))
    invalid_diffs = diffs - set(difficulties.keys())
    if invalid_diffs:
        raise ValueError(f"Invalid difficulties: {', '.join(invalid_diffs)}. Must be one of: {get_option_help(difficulties)}")
        
    # Validate modes
    modes_list = set(m.strip().lower() for m in args.modes.split(','))
    invalid_modes = modes_list - set(modes.keys())
    if invalid_modes:
        raise ValueError(f"Invalid modes: {', '.join(invalid_modes)}. Must be one of: {get_option_help(modes)}")
        
    # Validate events
    events_list = set(e.strip().lower() for e in args.events.split(','))
    invalid_events = events_list - set(events.keys())
    if invalid_events:
        raise ValueError(f"Invalid events: {', '.join(invalid_events)}. Must be one of: {get_option_help(events)}")
        
    # Validate model tag
    if args.model_tag not in model_tags:
        raise ValueError(f"Invalid model tag: {args.model_tag}. Must be one of: {get_option_help(model_tags)}")

    # Handle output directory
    if args.output is None:
        if args.input.is_file():
            args.output = args.input.parent
        else:
            args.output = args.input

def process_files(audio_files: List[Path], args: argparse.Namespace) -> None:
    """
    Process a list of audio files.
    
    Args:
        audio_files: List of audio files to process
        args: Parsed command line arguments
    """
    total_files = len(audio_files)
    
    # Map all options to their canonical values
    mapped_diffs = ",".join([difficulties[x] for x in args.difficulties.split(',')])
    mapped_modes = ",".join([modes[x] for x in args.modes.split(',')])  
    mapped_events = ",".join([events[x] for x in args.events.split(',')])
    mapped_env = environments[args.environment]
    mapped_tag = model_tags[args.model_tag]
    
    # Print a colorful summary of the mapping options
    print(f"\n{BOLD}🎵 Beatmap Generation Options:{RESET}")
    print(f"  {CYAN}🎚️ Difficulties:{RESET} {GREEN}{mapped_diffs}{RESET}")
    print(f"  {CYAN}🎮 Game Modes:{RESET} {GREEN}{mapped_modes}{RESET}")
    print(f"  {CYAN}💡 Events:{RESET} {GREEN}{mapped_events}{RESET}")
    print(f"  {CYAN}🌍 Environment:{RESET} {GREEN}{mapped_env}{RESET}")
    print(f"  {CYAN}🤖 Model:{RESET} {GREEN}{mapped_tag}{RESET}")
    if args.use_patreon:
        print(f"  {CYAN}🎭 Patreon:{RESET} {GREEN}Required{RESET}")
    print(f"{BOLD}---------------------------{RESET}\n")
    
    for idx, file in enumerate(audio_files, 1):
        print(f"\n{BOLD}Processing file {idx}/{total_files}: {BLUE}{file.name}{RESET}")
        try:
            get_map(file, args.output, mapped_diffs, mapped_modes,
                   mapped_events, mapped_env, mapped_tag, args.use_patreon)
        except Exception as e:
            print(f"{YELLOW}{WARNING} Error processing {file.name}: {str(e)}{RESET}")
            continue

if __name__ == '__main__':
    try:
        # Parse arguments
        args = get_args()
        
        # Validate arguments
        validate_args(args)

        # ensure output directory exists and is writable
        args.output.mkdir(parents=True, exist_ok=True)
        if not os.access(args.output, os.W_OK):
            raise PermissionError(f"Output directory is not writable: {args.output}")
    
        # Print output directory information
        print(f"\n{BOLD}📁 Output Directory:{RESET} {CYAN}{args.output}{RESET}")
 
        # Prepare input files
        audio_files = prepare_input_files(args.input)
        
        # Process files
        process_files(audio_files, args)
        
        print(f"\n{GREEN}{SUCCESS} All files processed! {DONE}{RESET}")
    except Exception as e:
        print(f"{YELLOW}{ERROR} Error: {str(e)}{RESET}", file=sys.stderr)
        sys.exit(1)
