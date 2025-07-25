
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
