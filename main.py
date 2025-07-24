import os
import secrets
import requests
import json
from flask import Flask, request, redirect, session, jsonify
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a random secret key

# Spotify OAuth configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = 'http://127.0.0.1:8080/oauth/callback'
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE = 'https://api.spotify.com/v1'
SCOPES = 'playlist-read-private playlist-read-collaborative'

def make_spotify_request(endpoint, access_token):
    """Make authenticated request to Spotify API"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f"{SPOTIFY_API_BASE}{endpoint}", headers=headers)
    response.raise_for_status()
    return response.json()

def fetch_all_playlists(access_token, user_id):
    """Fetch all playlists for a user with pagination"""
    playlists = []
    url = f"/users/{user_id}/playlists"
    
    while url:
        print(f"Fetching playlists batch...")
        data = make_spotify_request(url.replace(SPOTIFY_API_BASE, ''), access_token)
        playlists.extend(data['items'])
        url = data['next']  # Next page URL or None
        
    return playlists

def fetch_playlist_tracks(playlist_id, access_token):
    """Fetch all tracks for a specific playlist with pagination"""
    tracks = []
    url = f"/playlists/{playlist_id}/tracks"
    
    while url:
        print(f"  Fetching tracks for playlist {playlist_id}...")
        data = make_spotify_request(url.replace(SPOTIFY_API_BASE, ''), access_token)
        tracks.extend(data['items'])
        url = data['next']  # Next page URL or None
        
    return tracks

@app.route('/')
def index():
    """Home page with login link"""
    return '''
    <h1>Spotify Playlist Ripper</h1>
    <p>Click the link below to authenticate with Spotify:</p>
    <a href="/login">Login with Spotify</a>
    '''

@app.route('/login')
def login():
    """Redirect to Spotify authorization"""
    # Generate a random state parameter for security
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    
    # Build authorization URL
    auth_params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
        'state': state
    }
    
    auth_url = f"{SPOTIFY_AUTH_URL}?{urlencode(auth_params)}"
    return redirect(auth_url)

@app.route('/oauth/callback')
def callback():
    """Handle OAuth callback from Spotify"""
    
    # Verify state parameter
    state = request.args.get('state')
    if state != session.get('oauth_state'):
        return '<h1>Error:</h1><p>Invalid state parameter</p>'
    
    # Get authorization code
    code = request.args.get('code')
    if not code:
        return '<h1>Error:</h1><p>No authorization code received</p>'
    
    # Exchange code for access token
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    
    try:
        response = requests.post(SPOTIFY_TOKEN_URL, data=token_data)
        response.raise_for_status()
        token_info = response.json()
        
        access_token = token_info.get('access_token')
        refresh_token = token_info.get('refresh_token')
        expires_in = token_info.get('expires_in')
        
        # Store access token in session for later use
        session['access_token'] = access_token
        
        # Print the access token to console
        print("="*50)
        print("SPOTIFY OAUTH SUCCESS!")
        print("="*50)
        print(f"Access Token: {access_token}")
        print(f"Refresh Token: {refresh_token}")
        print(f"Expires in: {expires_in} seconds")
        print("="*50)
        
        return f'''
        <h1>OAuth Success!</h1>
        <p>Successfully authenticated with Spotify!</p>
        <p><strong>Access Token:</strong> {access_token[:20]}...</p>
        <p><strong>Token expires in:</strong> {expires_in} seconds</p>
        <p>Check your console for the full access token.</p>
        <p><a href="/fetch-data">🎵 Fetch My Playlists</a></p>
        <a href="/">Go back home</a>
        '''
        
    except requests.exceptions.RequestException as e:
        print(f"Error exchanging code for token: {e}")
        return f'<h1>Error:</h1><p>Failed to exchange code for token: {e}</p>'

@app.route('/fetch-data')
def fetch_data():
    """Fetch user data, playlists, and all playlist tracks"""
    access_token = session.get('access_token')
    if not access_token:
        return '<h1>Error:</h1><p>No access token found. Please <a href="/login">login</a> first.</p>'
    
    try:
        print("\n" + "="*60)
        print("STARTING SPOTIFY DATA FETCH")
        print("="*60)
        
        # 1. Get user profile
        print("🔍 Fetching user profile...")
        user_data = make_spotify_request('/me', access_token)
        user_id = user_data['id']
        print(f"✅ User found: {user_data['display_name']} (ID: {user_id})")
        
        # 2. Get all playlists
        print(f"\n🎵 Fetching playlists for user {user_id}...")
        playlists = fetch_all_playlists(access_token, user_id)
        print(f"✅ Found {len(playlists)} playlists")
        
        # 3. Get tracks for each playlist
        print(f"\n🎶 Fetching tracks for all playlists...")
        playlist_data = []
        
        for i, playlist in enumerate(playlists, 1):
            playlist_id = playlist['id']
            playlist_name = playlist['name']
            playlist_owner = playlist['owner']['display_name']
            track_count = playlist['tracks']['total']
            
            print(f"\n[{i}/{len(playlists)}] Processing: '{playlist_name}' by {playlist_owner} ({track_count} tracks)")
            
            # Fetch all tracks for this playlist
            tracks = fetch_playlist_tracks(playlist_id, access_token)
            
            # Structure the playlist data
            structured_playlist = {
                'id': playlist_id,
                'name': playlist_name,
                'description': playlist.get('description', ''),
                'owner': playlist_owner,
                'owner_id': playlist['owner']['id'],
                'public': playlist['public'],
                'collaborative': playlist['collaborative'],
                'total_tracks': track_count,
                'fetched_tracks': len(tracks),
                'external_urls': playlist['external_urls'],
                'tracks': []
            }
            
            # Process each track
            for track_item in tracks:
                if track_item['track'] and track_item['track']['type'] == 'track':
                    track = track_item['track']
                    track_data = {
                        'id': track['id'],
                        'name': track['name'],
                        'artists': [artist['name'] for artist in track['artists']],
                        'album': track['album']['name'],
                        'duration_ms': track['duration_ms'],
                        'explicit': track['explicit'],
                        'popularity': track['popularity'],
                        'external_urls': track['external_urls'],
                        'preview_url': track.get('preview_url'),
                        'added_at': track_item.get('added_at')
                    }
                    structured_playlist['tracks'].append(track_data)
            
            playlist_data.append(structured_playlist)
            print(f"  ✅ Processed {len(structured_playlist['tracks'])} valid tracks")
        
        # Create final structured data
        final_data = {
            'user': {
                'id': user_data['id'],
                'display_name': user_data['display_name'],
                'email': user_data.get('email'),
                'country': user_data.get('country'),
                'followers': user_data['followers']['total'],
                'external_urls': user_data['external_urls']
            },
            'playlists': playlist_data,
            'summary': {
                'total_playlists': len(playlist_data),
                'total_tracks': sum(len(p['tracks']) for p in playlist_data),
                'fetch_timestamp': str(requests.get('http://worldtimeapi.org/api/timezone/UTC').json()['datetime'])
            }
        }
        
        # Save to JSON file
        filename = f"spotify_data_{user_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 SUCCESS! Data saved to {filename}")
        print("="*60)
        
        # Return summary page
        total_tracks = final_data['summary']['total_tracks']
        total_playlists = final_data['summary']['total_playlists']
        
        return f'''
        <h1>✅ Data Fetch Complete!</h1>
        <h2>Summary:</h2>
        <ul>
            <li><strong>User:</strong> {user_data['display_name']}</li>
            <li><strong>Playlists:</strong> {total_playlists}</li>
            <li><strong>Total Tracks:</strong> {total_tracks}</li>
            <li><strong>Saved to:</strong> {filename}</li>
        </ul>
        <p>Check your console for detailed progress and the JSON file for complete data!</p>
        <p><a href="/">🏠 Go Home</a> | <a href="/fetch-data">🔄 Fetch Again</a></p>
        '''
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        return f'<h1>Error:</h1><p>Failed to fetch data: {e}</p><p><a href="/">Go back home</a></p>'
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return f'<h1>Error:</h1><p>Unexpected error: {e}</p><p><a href="/">Go back home</a></p>'

if __name__ == '__main__':
    PORT = 8080
    # Check if environment variables are set
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print(".env variables SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not configured correctly")
        exit(1)
    
    print("Starting Spotify Playlist Ripper...")
    print(f"Server running at: http://127.0.0.1:{PORT}")
    
    app.run(host='127.0.0.1', port=PORT, debug=True)