import os
import sys
import yt_dlp

def download_mps(tracks, OUTPUT_FOLDER):
    
    OUTPUT_FOLDER = os.path.join(OUTPUT_FOLDER, "tracks")
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    if not tracks or len(tracks) == 0:
        print("No tracks to download.")
        return
    
    processed_tracks = []
    
    class PostDownloadProcessor(yt_dlp.postprocessor.PostProcessor):
        def run(self, info):
            processed_tracks.append(track)
            #rename file based on tracks
            yt_id = info.get('id')
            track = next((track for track in tracks if track.get('yt_id') == yt_id), None)
            new_filename = f"{OUTPUT_FOLDER}/{track.get('id')}.{info['ext']}"
            old_file_name = f"{OUTPUT_FOLDER}/{yt_id}.{info['ext']}"
            #rename
            if os.path.exists(old_file_name):
                os.rename(old_file_name, new_filename)
            sys.stdout.write(f"({len(processed_tracks)}/{len(tracks)}) Completed - just downloaded {track.get('track_name')} by {track.get('artists')}.")
            sys.stdout.flush()
            return [], info
    
    URLS = [track.get('youtube_url') for track in tracks if track.get('youtube_url')]
    ydl_opts = {
        'quiet': True,
        'format': 'bestaudio/best',
        'outtmpl': f"{OUTPUT_FOLDER}/%(id)s.%(ext)s", # output filname as id.mp3
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',    # Convert to mp3
                'preferredquality': '192', 
            }
        ]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.add_post_processor(PostDownloadProcessor(), when='post_process')
        ydl.download(URLS)