from process_spotify import process_spotify_playlists
from search_yt import search_youtube_videos
from yt_mp3 import download_mps

import os

OUTPUT_FOLDER = os.path.join(os.getcwd(), "tracks")

def processor():
    #extract command line arg
    import sys
    if len(sys.argv) < 2:
        print("Usage: python search-yt.py <input_file>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    
    # read input json file
    import json
    print(f"Reading input file: {input_file}")
    with open(input_file, 'r') as f:
        spotify_data = json.load(f) #set global variable
    
    tracks = process_spotify_playlists(spotify_data)  
    print(f"Extracted {len(tracks)} tracks from the input file.")
    if not tracks:
        return
    
    #get youtube videos for each track
    print(f"Beginning searching of YouTube videos for {len(tracks)} tracks...")
    skipped_tracks = []
    unfound_tracks = []
    for track in tracks:
        track_name = track.get('track_name')
        artists = track.get('artists')
        if not track_name or not artists:
            skipped_tracks.append(track)
            continue
        
        video_info = search_youtube_videos(track_name, artists)
        if video_info:
            track['yt_url'] = video_info.get('yt_url')
            track['yt_id'] = video_info.get('yt_id')
        else:
            unfound_tracks.append(track)
            
    print(f"Found {len(tracks) - (len(unfound_tracks) + len(skipped_tracks))}/ {len(tracks)} tracks with YouTube videos.")
    if skipped_tracks:
        print(f"Skipped {len(skipped_tracks)} tracks due to missing track_name or artists.")
    if unfound_tracks:
        print(f"Could not find YouTube videos for {len(unfound_tracks)} tracks.")
        
    print("Beginning download of YouTube videos as MP3 files...")
    download_mps(tracks, OUTPUT_FOLDER)
    
if __name__ == '__main__':
    processor()
    print("Processing complete, all tracks downloaded to:", OUTPUT_FOLDER)
    
    
    