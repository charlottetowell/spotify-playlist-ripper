import os
import yt_dlp


def download_mps(tracks, OUTPUT_FOLDER):
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        
    if not tracks or len(tracks) == 0:
        print("No tracks to download.")
        return
    
    class PostDownloadProcessor(yt_dlp.postprocessor.PostProcessor):
        def run(self, info):
            print(f"Post-processing {info['id']}...")
            #rename file based on tracks
            yt_id = info.get('id')
            track = next((track for track in tracks if track.get('yt_id') == yt_id), None)
            new_filename = f"{OUTPUT_FOLDER}/{track.get('track_name')}.mp3"
            old_file_name = f"{OUTPUT_FOLDER}/{yt_id}.{info['ext']}"
            #rename
            if os.path.exists(old_file_name):
                os.rename(old_file_name, new_filename)
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
        # commenting out - this will instead be handled in playlist folder builder
        #ydl.add_post_processor(PostDownloadProcessor(), when='post_process')
        ydl.download(URLS)