# Simple Auto BeatSage Script

A Python script for automatically generating Beat Saber maps from local music files using [Beat Sage](https://beatsage.com/).

> **Note:** This is a fork of [rote66/simple_auto_beatsage_script](https://github.com/rote66/simple_auto_beatsage_script). This project is not officially affiliated with Beat Sage.

## Features

- Automate the process of creating Beat Saber maps from your local music files
- Support for multiple audio formats (mp3, ogg, flac, wav, m4a, opus, webm, weba, oga, mid, amr, aac, wma)
- Configurable difficulty levels, play modes, and environment settings
- Batch processing of entire music directories
- Automatic metadata extraction from audio files
- Smart filename generation using ID3 tags (Title - Artist format)
- Colorized terminal output with progress indicators 🎵
- Automatic zip extraction and cleanup
- Supports Patreon features via cookies if you are logged in/connected in your browser
- Automatic lighting events generation for enhanced visual experience

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
- Generate maps with Expert and ExpertPlus difficulties
- Include Standard mode
- Add DotBlocks and Obstacles as events
- Use the FitBeat environment
- Use the v2 model
- Save output zip files to the same input directory
- Generate automatic lighting events for enhanced visual experience

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
| `--difficulties` | `-d` | Comma-separated list of difficulties | Expert,ExpertPlus |
| `--modes` | `-m` | Comma-separated list of play modes | Standard |
| `--events` | `-e` | Comma-separated list of events | DotBlocks,Obstacles |
| `--environment` | `-env` | Environment for the generated maps | FitBeatEnvironment |
| `--model_tag` | `-t` | Model version to use | v2 |

### Available Environments

- DefaultEnvironment
- Origins
- TriangleEnvironment
- BigMirrorEnvironment
- NiceEnvironment
- DragonsEnvironment
- KDAEnvironment
- MonstercatEnvironment
- CrabRaveEnvironment
- PanicEnvironment
- RocketEnvironment
- GreenDayEnvironment
- GreenDayGrenadeEnvironment
- TimbalandEnvironment
- FitBeatEnvironment
- LinkinParkEnvironment
- BTSEnvironment
- KaleidoscopeEnvironment
- InterscopeEnvironment
- SkrillexEnvironment
- BillieEnvironment
- HalloweenEnvironment
- GagaEnvironment

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
2. For each file:
   - Extracts metadata (title, artist) from ID3 tags
   - Creates smart filenames based on metadata (Title - Artist)
   - Uploads the file to Beat Sage with your specified settings
   - Displays real-time progress with colorized indicators
   - Downloads the generated Beat Saber map
   - Automatically extracts the map to a named folder
   - Generates automatic lighting events for enhanced visuals
   - Cleans up temporary zip files
3. Provides clear visual feedback throughout the process with emojis and colors

## Enhanced User Interface

The script provides a rich terminal interface with:
- 🎵 Colorized output (when supported by your terminal)
- ⚙️ Real-time progress indicators
- ✨ Clear status messages
- 📁 Smart file organization
- ⏭️ Skip detection for existing maps
- 💡 Automatic lighting generation feedback
