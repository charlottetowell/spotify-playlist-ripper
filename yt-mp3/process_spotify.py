import os
import sys
import shutil


def process_spotify_playlists(spotify_data):        
    #validate structure of json
    if not isinstance(spotify_data, dict) or 'playlists' not in spotify_data:
        print("Invalid input file structure. Expected a dictionary with 'playlists' key.")
        return []
    if not isinstance(spotify_data['playlists'], list):
        print("Invalid input file structure. Expected 'playlists' to be a list.")
        return []
    if not spotify_data['playlists']:
        print("No playlists found in the input file.")
        return []
    if not all(isinstance(playlist, dict) for playlist in spotify_data['playlists']):
        print("Invalid input file structure. Each playlist should be a dictionary.")
        return []
    if not all('tracks' in playlist and isinstance(playlist['tracks'], list) for playlist in spotify_data['playlists']):
        print("Invalid input file structure. Each playlist should have a 'tracks' key with a list of tracks.")
        return []
    if not all('name' in track and 'artists' in track  and 'id' in track for playlist in spotify_data['playlists'] for track in playlist['tracks']):
        print("Invalid input file structure. Each track should have 'track_name', 'id' and 'artists' keys.")
        return []
        
    #get all unique tracks
    tracks = []
    for playlist in spotify_data.get('playlists', []):
        for track in playlist.get('tracks', []):
            track_name = track.get('name')
            artists = ', '.join(track.get('artists', []))
            album = track.get('album', '')
            track_id = track.get('id', '')
            if track_name and artists:
                #check if id not already in tracks
                if not any(t['id'] == track_id for t in tracks):
                    #add track to tracks
                    tracks.append({
                        "id": track_id,
                        "track_name": track_name,
                        "artists": artists,
                        "track_id": track_id,
                        "album": album
                    })
                
    return tracks


def build_spotify_playlists(spotify_data, OUTPUT_FOLDER):
    # Define the parent folder for all playlists
    parent_folder = os.path.join(OUTPUT_FOLDER, "playlists")
    os.makedirs(parent_folder, exist_ok=True)

    # Loop through each playlist in the Spotify data
    processed_playlists = 0
    for playlist in spotify_data.get('playlists', []):
        processed_playlists += 1
        playlist_name = playlist.get('name', 'Unnamed Playlist')
        playlist_folder = os.path.join(parent_folder, playlist_name)
        os.makedirs(playlist_folder, exist_ok=True)
        sys.stdout.write(f"\tProcessing playlist {playlist_name} - ({processed_playlists}/{len(spotify_data['playlists'])})")
        sys.stdout.flush()

        # Loop through each track in the playlist
        for track in playlist.get('tracks', []):
            track_id = track.get('id')
            track_name = track.get('name')
            artists = ', '.join(track.get('artists', []))

            # Find the corresponding MP3 file in the output folder
            source_file = os.path.join(f"{OUTPUT_FOLDER}/tracks", f"{track_id}.mp3")
            if os.path.exists(source_file):
                # Rename the file to "track_name - artists.mp3"
                new_file_name = f"{track_name} - {artists}.mp3"
                destination_file = os.path.join(playlist_folder, new_file_name)

                # Copy the file to the playlist folder
                shutil.copy2(source_file, destination_file)

    print(f"\nAll playlists have been organized in the folder: {parent_folder}")
    
    # #delete original /tracks folder in OUTPUT_FOLDER
    # shutil.rmtree(os.path.join(OUTPUT_FOLDER, "tracks"))
    # print("Temp /tracks folder deleted")