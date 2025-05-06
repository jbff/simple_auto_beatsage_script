# Simple Auto BeatSage Script

A Python script for automatically generating Beat Saber maps from local music files or YouTube videos using [Beat Sage](https://beatsage.com/).

> **Note:** This is a fork of [rote66/simple_auto_beatsage_script](https://github.com/rote66/simple_auto_beatsage_script). This project is not officially affiliated with Beat Sage.

## Features

- Automate the process of creating Beat Saber maps from your local music files or YouTube videos
- Support for multiple audio formats (mp3, ogg, flac, wav, m4a, opus, webm, weba, oga, mid, amr, aac, wma)
- Configurable difficulty levels, play modes, and environment settings
- Batch processing of entire music directories
- Process single audio files directly
- Download and process YouTube videos from a list of URLs
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
- tinytag==2.1.1
- yt-dlp==2025.4.30
- PyYAML==6.0.2

Additionally, for YouTube video processing, you need:
- ffmpeg (for audio conversion)

## Installation (Command Line Script)

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

4. Install ffmpeg (required for YouTube processing):
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # On Fedora
   sudo dnf install ffmpeg
   
   # On macOS (using Homebrew)
   brew install ffmpeg
   
   # On Windows (using Chocolatey)
   choco install ffmpeg
   ```

## Usage
### Command Line Script

Process all music files in a directory with default settings:

```bash
python bsdl.py -i /path/to/music/folder
```

Process a single audio file:

```bash
python bsdl.py -i /path/to/song.mp3
```

Process YouTube videos from a text file:

```bash
python bsdl.py -i /path/to/urls.txt
```

### Command Line (Windows Executable)

```cmd
bsdl.exe C:\path\to\music\folder
```

```cmd
bsdl.exe C:\path\to\song.mp3
```

```cmd
bsdl.exe C:\path\to\urls.txt
```

### Drag and Drop (Windows)

1. Copy `config_bsdl.yaml` to the same directory as the executable.

2. Edit `config_bsdl.yaml` to specify options to use when dragging/dropping.

3. Drag and drop any of the following onto the executable:
   - A directory containing audio files
   - A single audio file
   - A text file containing YouTube URLs (one per line)

## Example urls.txt:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://www.youtube.com/watch?v=oHg5SJYRHA0
```

### Advanced Usage

Customize the behavior with command-line arguments (these override config.yaml settings):

```bash
python bsdl.py -i /path/to/input -o /path/to/output/folder -d hard,exp -m std,noarrows -e dots,bombs1 -env nice -t flow
```

## Command-Line Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--input` | `-i` | Input path (directory of audio files, single audio file, or text file with YouTube URLs) | / |
| `--output` | `-o` | Output folder for the generated maps | Same as input directory for directories, or input file directory for files |
| `--difficulties` | `-d` | Comma-separated list of difficulties (normal/norm, hard, expert/exp, expertplus/explus) | expert,expertplus |
| `--modes` | `-m` | Comma-separated list of play modes (standard/std, 90degree/90deg, noarrows, onesaber) | standard |
| `--events` | `-e` | Comma-separated list of events (dotblocks/dots, obstacles/obs, bombs) | dotblocks,obstacles |
| `--environment` | `-env` | Environment name (default, origins, triangle, nice, bigmirror, dragons, kda, monstercat, crabrave, panic, rocket, greenday, greendaygrenade, timbaland, fitbeat, linkinpark) | default |
| `--model_tag` | `-t` | Model version (one/v1, two/v2, flow) | two |
| `--use-patreon` | `-P` | Require valid BeatSage cookie for Patreon features | false |

### Available Environments

- default (DefaultEnvironment)
- origins (Origins)
- triangle (TriangleEnvironment)
- nice (NiceEnvironment)
- bigmirror (BigMirrorEnvironment)
- dragons (DragonsEnvironment)
- kda (KDAEnvironment)
- monstercat (MonstercatEnvironment)
- crabrave (CrabRaveEnvironment)
- panic (PanicEnvironment)
- rocket (RocketEnvironment)
- greenday (GreenDayEnvironment)
- greendaygrenade (GreenDayGrenadeEnvironment)
- timbaland (TimbalandEnvironment)
- fitbeat (FitBeatEnvironment)
- linkinpark (LinkinParkEnvironment)

### Available Models

- one/v1 (Original model)
- two/v2 (Improved model)
- flow (Flow-based v2 model)

## Patreon Features

The script supports BeatSage Patreon features through browser cookies. To use Patreon features:

1. Log in to BeatSage in your browser
2. The script will automatically detect your session cookie
3. Use the `--use-patreon` flag to require Patreon features

If you're not a Patreon supporter, the script will still work with these limitations:
- File size limit: 32MB
- Song duration limit: 10 minutes

## Enhanced User Interface

The script provides a rich terminal interface with:
- 🎵 Colorized output (when supported by your terminal)
- ⚙️ Real-time progress indicators
- ✨ Clear status messages
- 📁 Smart file organization
- ⏭️ Skip detection for existing maps
- 💡 Automatic lighting generation feedback
- 🔍 Detailed option mapping display
- 🎭 Patreon status indicators

## Acknowledgments

This project is a fork of [rote66/simple_auto_beatsage_script](https://github.com/rote66/simple_auto_beatsage_script) and includes logic for automatic lighting events from [ItsOrius/LiteMapper](https://github.com/ItsOrius/LiteMapper). I am grateful for their contributions to the Beat Saber mapping community.
