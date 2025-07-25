import yt_dlp

URLS = ['https://www.youtube.com/watch?v=1leInEAlbjY']

def download_mps():
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(id)s.%(ext)s', # output filname as id.mp3
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',    # Convert to mp3
                'preferredquality': '192', 
            }
        ]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(URLS)
        
if __name__ == '__main__':
    download_mps()