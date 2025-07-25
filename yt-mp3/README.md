# Youtube to MP3 Converter

- Parse spotify extract
- Find valid URLs for each track
- Download each track
- Organse folder structure to match playlists

### Installation
* Install [yt-dlp](https://github.com/yt-dlp/yt-dlp) library via `pip install yt-dlp[default]`
* Install ffmpeg via `scoop install ffmpeg`

### How to Use
1. Use the spotify extractor tool so you have a `.json` file
2. Run the python script as follows:
```
python yt-mp3/main.py <INPUT_FILE>.json
```