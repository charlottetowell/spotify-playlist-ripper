# Youtube to MP3 Converter

This python script can be used to go from Spotify playlist & track export, to an organise folder structure of downloaded MP3 files.

> Note: it is illegal to *distribute* downloaded content, only use for personal use

### Installation
* Install [yt-dlp](https://github.com/yt-dlp/yt-dlp) library via `pip install yt-dlp[default]`
* Install ffmpeg via `scoop install ffmpeg`

### How to Use
1. Use the spotify extractor tool so you have a `.json` file
2. Run the python script as follows:
```
python yt-mp3/main.py <INPUT_FILE>.json
```