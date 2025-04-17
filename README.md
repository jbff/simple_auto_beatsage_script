# Simple Auto BeatSage Script

A Python script for automatically generating Beat Saber maps from local music files using [Beat Sage](https://beatsage.com/).

> **Note:** This is a fork of [rote66/simple_auto_beatsage_script](https://github.com/rote66/simple_auto_beatsage_script). This project is not officially affiliated with Beat Sage.

## Features

- Automate the process of creating Beat Saber maps from your local music files
- Support for multiple audio formats (mp3, ogg, flac, wav, m4a, etc.)
- Configurable difficulty levels, play modes, and environment settings
- Batch processing of entire music directories
- Automatic metadata extraction from audio files
- Supports Patreon features via cookies if you are logged in/connected in your browser

## Dependencies

The script requires the following Python packages:

- browsercookie==0.8.1
- requests==2.32.3
- tinytag==2.1.0

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/jbff/simple_auto_beatsage_script.git
   cd simple_auto_beatsage_script
   ```

2. Set up a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Simple Usage

Process all music files in a directory with default settings:

```bash
python main.py -i /path/to/music/folder
```

This will:
- Process all supported audio files in the specified directory
- Generate maps with Hard, Expert, ExpertPlus, and Normal difficulties
- Include Standard, 90Degree, NoArrows, and OneSaber modes
- Add DotBlocks, Obstacles, and Bombs as events
- Use the v2 model
- Save output zip files to the same input directory

### Advanced Usage

Customize the behavior with command-line arguments:

```bash
python main.py -i /path/to/music/folder -o /path/to/output/folder -d Hard,Expert -m Standard -e DotBlocks -env DefaultEnvironment -t v2
```

## Command-Line Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--input` | `-i` | Input folder containing music files (required) | / |
| `--output` | `-o` | Output folder for the generated maps | Same as input folder |
| `--difficulties` | `-d` | Comma-separated list of difficulties | Hard,Expert,ExpertPlus,Normal |
| `--modes` | `-m` | Comma-separated list of play modes | Standard,90Degree,NoArrows,OneSaber |
| `--events` | `-e` | Comma-separated list of events | DotBlocks,Obstacles,Bombs |
| `--environment` | `-env` | Environment for the generated maps | DefaultEnvironment |
| `--model_tag` | `-t` | Model version to use | v2 |

### Available Environments

- DefaultEnvironment
- Origins (Origins)
- TriangleEnvironment (Triangle)
- NiceEnvironment (Nice)
- BigMirrorEnvironment (Big Mirror)
- DragonsEnvironment (Imagine Dragons)
- KDAEnvironment (K/DA)
- MonstercatEnvironment (Monstercat)
- CrabRaveEnvironment (Crab Rave)
- PanicEnvironment (Panic at the Disco!)
- RocketEnvironment (Rocket League)
- GreenDayEnvironment (Green Day)
- GreenDayGrenadeEnvironment (Green Day Grenade)
- TimbalandEnvironment (Timbaland)
- FitBeatEnvironment (FitBeat)
- LinkinParkEnvironment (Linkin Park)

### Available Models

- v1 (Original model)
- v2 (Improved model)
- v2-flow (Flow-based v2 model)

## Limitations

- File size limit: 32MB
- Song duration limit: 10 minutes
- These limits apply to non-Patreon supporters of Beat Sage

## How It Works

The script:
1. Scans the input directory for compatible audio files
2. Extracts metadata (title, artist, cover art) from each file
3. Uploads the file to Beat Sage with your specified settings
4. Polls for completion
5. Downloads the generated Beat Saber map as a zip file to the output directory

