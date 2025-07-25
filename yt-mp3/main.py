from process_spotify import process_spotify_playlists, build_spotify_playlists
from search_yt import search_youtube_videos
from yt_mp3 import download_mps

import os
import json

OUTPUT_FOLDER = os.path.join(os.getcwd(), "music")

def processor():
    # Extract command line argument
    import sys
    if len(sys.argv) < 2:
        print("Usage: python search-yt.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]

    # Read the input file
    print(f"Reading input file: {input_file}")
    with open(input_file, 'r') as f:
        spotify_data = json.load(f)

    # Process Spotify playlists
    print("Processing Spotify playlists...")
    tracks = process_spotify_playlists(spotify_data)
    print(f"\tExtracted {len(tracks)} tracks from the input file.")

    # Search YouTube videos
    print(f"Searching YouTube videos for {len(tracks)} tracks...")
    skipped_tracks = []
    unfound_tracks = []
    for i, track in enumerate(tracks, start=1):
        track_name = track.get('track_name')
        artists = track.get('artists')
        sys.stdout.write(f"\r\tSearching track {i}/{len(tracks)}")
        sys.stdout.flush()
        if not track_name or not artists:
            skipped_tracks.append(track)
            continue

        video_info = search_youtube_videos(track_name, artists)
        if video_info:
            track['yt_url'] = video_info.get('yt_url')
            track['yt_id'] = video_info.get('yt_id')
        else:
            unfound_tracks.append(track)
            
    print(f"\nFound YouTube videos for {len(tracks) - (len(unfound_tracks) + len(skipped_tracks))} tracks.")
    if skipped_tracks:
        print(f"Skipped {len(skipped_tracks)} tracks due to missing track_name or artists.")
    if unfound_tracks:
        print(f"Could not find YouTube videos for {len(unfound_tracks)} tracks.")

    # Download MP3s
    print(f"Downloading MP3s for {len(tracks)} tracks...")
    download_mps(tracks, OUTPUT_FOLDER)
    print("All MP3s downloaded successfully.")

    # Build Spotify playlists
    print("Organizing tracks into Spotify playlists...")
    build_spotify_playlists(spotify_data, OUTPUT_FOLDER)
    print("Playlists organized successfully.")

if __name__ == '__main__':
    processor()
    print("Done :)")


