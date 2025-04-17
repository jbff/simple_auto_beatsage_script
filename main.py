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
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

import browsercookie
import requests
from tinytag import TinyTag

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
        cover = tag.get_image() or b''
        return title, artist, cover
    except Exception as e:
        raise RuntimeError(f"Failed to read MP3 tags from {file}: {str(e)}")

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
    """
    try:
        audio_title, audio_artist, cover_art = get_mp3_tag(file)
        filename = Path(file).stem
        if not audio_title:
            audio_title = filename
            
        print(f'Processing file: "{filename}"')
        
        payload = {
            'audio_metadata_title': audio_title,
            'audio_metadata_artist': audio_artist,
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
        
        response = session.post(create_url, headers=headers_beatsage, data=payload, files=files)
        
        if response.status_code == 413:
            raise RuntimeError("File size or song length limit exceeded (32MB, 10min for non-Patreon supporters)")
            
        response.raise_for_status()
        
        map_id = json.loads(response.text)['id']
        heart_url = f"{base_url}/beatsaber_custom_level_heartbeat/{map_id}"
        download_url = f"{base_url}/beatsaber_custom_level_download/{map_id}"
        
        print("Processing", end='', flush=True)
        max_attempts = 60  # 3 minutes maximum
        attempt = 0
        
        while attempt < max_attempts:
            heartbeat_response = session.get(heart_url, headers=headers_beatsage)
            heartbeat_response.raise_for_status()
            status = json.loads(heartbeat_response.text)['status']
            
            if status == "DONE":
                break
            elif status == "ERROR":
                raise RuntimeError("Map generation failed")
                
            time.sleep(3)
            print('.', end='', flush=True)
            attempt += 1
        else:
            raise RuntimeError("Map generation timed out")
            
        print('\nFile processing complete\n---------------------------\n')
        
        response = session.get(download_url, headers=headers_beatsage)
        response.raise_for_status()
        
        output_path = Path(outputdir) / f"{filename}.zip"
        output_path.write_bytes(response.content)
        
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
    parser = argparse.ArgumentParser(description='Simple auto beatsage from local files by rote66')
    parser.add_argument('--input', '-i', type=Path, required=True,
                       help='Input folder containing audio files')
    parser.add_argument('--output', '-o', type=Path, default=None,
                       help='Output folder for generated maps (defaults to input folder)')
    parser.add_argument('--difficulties', '-d', type=str, default='Hard,Expert,ExpertPlus,Normal',
                       help='Comma-separated difficulties: Hard,Expert,ExpertPlus,Normal')
    parser.add_argument('--modes', '-m', type=str, default='Standard,90Degree,NoArrows,OneSaber',
                       help='Comma-separated modes: Standard,90Degree,NoArrows,OneSaber')
    parser.add_argument('--events', '-e', type=str, default='DotBlocks,Obstacles,Bombs',
                       help='Comma-separated events: DotBlocks,Obstacles,Bombs')
    parser.add_argument('--environment', '-env', type=str, default='DefaultEnvironment',
                       help='Environment name (e.g., DefaultEnvironment, Origins, etc.)')
    parser.add_argument('--model_tag', '-t', type=str, default='v2',
                       help='Model version: v1, v2, v2-flow')
    
    # Handle the case where a single argument is provided (assumed to be input path)
    if len(sys.argv) == 2 and Path(sys.argv[1]).exists():
        return parser.parse_args(['-i', sys.argv[1]])
    return parser.parse_args()

def process_files(args: argparse.Namespace) -> None:
    """
    Process all audio files in the input directory.
    
    Args:
        args: Parsed command line arguments
        
    Raises:
        FileNotFoundError: If input directory doesn't exist
        RuntimeError: If processing fails for any file
        
    The function will:
    1. Validate input and output directories
    2. Find all supported audio files
    3. Process each file, skipping existing outputs
    4. Handle errors for individual files without stopping the entire process
    """
    if not args.input.exists():
        raise FileNotFoundError(f"Input directory does not exist: {args.input}")
        
    if args.output is None:
        args.output = args.input
    else:
        args.output.mkdir(parents=True, exist_ok=True)
        
    # Define supported audio extensions
    audio_extensions = {'.opus', '.flac', '.webm', '.weba', '.wav', '.ogg', 
                       '.m4a', '.mp3', '.oga', '.mid', '.amr', '.aac', '.wma'}
    
    # Find all audio files
    audio_files = [f for f in args.input.iterdir() 
                  if f.suffix.lower() in audio_extensions]
    
    if not audio_files:
        print(f"No audio files found in {args.input}")
        return
        
    total_files = len(audio_files)
    print(f"Found {total_files} audio files to process")
    
    for idx, file in enumerate(audio_files, 1):
        output_zip = args.output / f"{file.stem}.zip"
        if output_zip.exists():
            print(f"Skipping {file.name} - output already exists")
            continue
            
        print(f"\nProcessing file {idx}/{total_files}: {file.name}")
        try:
            get_map(file, args.output, args.difficulties, args.modes,
                   args.events, args.environment, args.model_tag)
        except Exception as e:
            print(f"Error processing {file.name}: {str(e)}")
            continue

if __name__ == '__main__':
    try:
        args = get_args()
        process_files(args)
        print('\nAll files processed!')
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
