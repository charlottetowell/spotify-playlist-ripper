from process_spotify import process_spotify_playlists
from search_yt import search_youtube_videos
from yt_mp3 import download_mps

import os
import tempfile
import json

OUTPUT_FOLDER = os.path.join(os.getcwd(), "tracks")

def processor():
    #extract command line arg
    import sys
    if len(sys.argv) < 2:
        print("Usage: python search-yt.py <input_file>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    
    # Define the path for the temporary file
    temp_file_path = os.path.join(tempfile.gettempdir(), "spotify_data_backup.json")

    # Update the backup file with the current step
    def update_backup_file(data, step):
        data['CURRENT_STEP'] = step
        with open(temp_file_path, 'w') as temp_file:
            json.dump(data, temp_file)

    # Check if temp file exists and prompt user
    if os.path.exists(temp_file_path):
        print(f"A backup file was found at {temp_file_path}.")
        user_input = input("Do you want to resume from the backup? (Y/N): ").strip().lower()
        if user_input == 'y':
            print("Resuming from backup...")
            with open(temp_file_path, 'r') as temp_file:
                backup_data = json.load(temp_file)
                current_step = backup_data.get('CURRENT_STEP', 'START')
                print(f"Resuming from step: {current_step}")
        elif user_input == 'n':
            print("Starting fresh and overwriting backup...")
            os.remove(temp_file_path)
            backup_data = {'CURRENT_STEP': 'START'}
        else:
            print("Invalid input. Exiting.")
            sys.exit(1)
    else:
        backup_data = {'CURRENT_STEP': 'START'}

    # Save spotify_data to temp file after reading input
    print(f"Reading input file: {input_file}")
    with open(input_file, 'r') as f:
        spotify_data = json.load(f)

    backup_data['spotify_data'] = spotify_data
    update_backup_file(backup_data, 'START')

    # Process Spotify playlists if not already done
    if backup_data['CURRENT_STEP'] == 'START':
        print("Processing Spotify playlists...")
        tracks = process_spotify_playlists(spotify_data)
        print(f"\tExtracted {len(tracks)} tracks from the input file.")
        backup_data['tracks'] = tracks
        update_backup_file(backup_data, 'PROCESSED_SPOTIFY')
    else:
        tracks = backup_data.get('tracks', [])
        print(f"Resuming with {len(tracks)} tracks already processed from Spotify playlists.")

    # Search YouTube videos if not already done
    if backup_data['CURRENT_STEP'] == 'PROCESSED_SPOTIFY':
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

        print()  # Move to the next line after progress
        print(f"Found YouTube videos for {len(tracks) - (len(unfound_tracks) + len(skipped_tracks))} tracks.")
        if skipped_tracks:
            print(f"Skipped {len(skipped_tracks)} tracks due to missing track_name or artists.")
        if unfound_tracks:
            print(f"Could not find YouTube videos for {len(unfound_tracks)} tracks.")

        backup_data['tracks'] = tracks
        update_backup_file(backup_data, 'SEARCHED_SONGS')

    # Download MP3s if not already done
    if backup_data['CURRENT_STEP'] == 'SEARCHED_SONGS':
        print(f"Downloading MP3s for {len(tracks)} tracks...")
        download_mps(tracks, OUTPUT_FOLDER)
        print("All MP3s downloaded successfully.")
        update_backup_file(backup_data, 'DOWNLOADED_MP3S')

    # Clean up temp file at the end of processing
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
        print(f"Temporary backup file {temp_file_path} deleted.")
        
if __name__ == '__main__':
    processor()
    print("Processing complete, all tracks downloaded to:", OUTPUT_FOLDER)


