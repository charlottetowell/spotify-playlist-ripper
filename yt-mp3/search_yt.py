from yt_dlp import YoutubeDL

def find_youtube_video(song_name, artists):
    query = f'ytsearch1:{song_name} {artists}'
    ydl_opts = {
        'quiet': True,
        'skip_download': True, #dont download
    }
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            entries = info.get('entries', [])
            if not entries:
                print("No entries found for the query.")
                return None
            return {
                "url": entries[0].get('webpage_url'),
                "id": entries[0].get('id'),
            }
        except Exception as e:
            return None