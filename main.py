import os
import secrets
import requests
import json
import time
from flask import Flask, request, redirect, session, jsonify, send_file, render_template
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

# Update make_spotify_request to check token validity
def make_spotify_request(endpoint, access_token):
    """Make authenticated request to Spotify API, checking token validity"""
    # Check if token is expired
    if 'token_expires_at' in session and time.time() >= session['token_expires_at']:
        print("Access token expired. Redirecting to login.")
        return redirect('/login')

    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f"{SPOTIFY_API_BASE}{endpoint}", headers=headers)

    # Handle token expiration errors from Spotify API
    if response.status_code == 401:
        print("Access token invalid or expired. Redirecting to login.")
        return redirect('/login')

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
    return render_template('index.html')

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

        # Store access token and expiration time in session
        session['access_token'] = access_token
        session['refresh_token'] = refresh_token
        session['token_expires_at'] = time.time() + expires_in

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

@app.route('/fetch-data', methods=['GET', 'POST'])
def fetch_data():
    """Fetch user data and display playlists for selection"""
    access_token = session.get('access_token')
    if not access_token:
        return '<h1>Error:</h1><p>No access token found. Please <a href="/login">login</a> first.</p>'

    if request.method == 'POST':
        # Process selected playlists
        selected_playlists = request.form.getlist('playlists')
        if not selected_playlists:
            return '<h1>Error:</h1><p>No playlists selected. Please go back and select at least one playlist.</p>'

        try:
            print("\n" + "="*60)
            print("STARTING SPOTIFY DATA FETCH FOR SELECTED PLAYLISTS")
            print("="*60)

            playlist_data = []

            for i, playlist_id in enumerate(selected_playlists, 1):
                print(f"\n[{i}/{len(selected_playlists)}] Fetching tracks for playlist ID: {playlist_id}")

                # Fetch playlist details
                playlist = make_spotify_request(f'/playlists/{playlist_id}', access_token)
                tracks = fetch_playlist_tracks(playlist_id, access_token)

                structured_playlist = {
                    'id': playlist_id,
                    'name': playlist['name'],
                    'description': playlist.get('description', ''),
                    'owner': playlist['owner']['display_name'],
                    'owner_id': playlist['owner']['id'],
                    'public': playlist['public'],
                    'collaborative': playlist['collaborative'],
                    'total_tracks': playlist['tracks']['total'],
                    'fetched_tracks': len(tracks),
                    'external_urls': playlist['external_urls'],
                    'tracks': []
                }

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

            # Save to JSON file
            user_data = make_spotify_request('/me', access_token)
            filename = f"spotify_data_{user_data['id']}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({'playlists': playlist_data}, f, indent=2, ensure_ascii=False)

            print(f"\n🎉 SUCCESS! Data saved to {filename}")
            print("="*60)

            return render_template('summary.html', playlists_processed=len(playlist_data), filename=filename)

        except requests.exceptions.RequestException as e:
            print(f"❌ API Error: {e}")
            return f'<h1>Error:</h1><p>Failed to fetch data: {e}</p><p><a href="/">Go back home</a></p>'
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return f'<h1>Error:</h1><p>Unexpected error: {e}</p><p><a href="/">Go back home</a></p>'

    else:
        # Display playlists for selection
        try:
            print("\n" + "="*60)
            print("FETCHING USER PLAYLISTS FOR SELECTION")
            print("="*60)

            user_data = make_spotify_request('/me', access_token)
            user_id = user_data['id']
            playlists = fetch_all_playlists(access_token, user_id)

            playlist_options = ''.join(
                f'<li><input type="checkbox" name="playlists" value="{p["id"]}"> {p["name"]} ({p["tracks"]["total"]} tracks)</li>'
                for p in playlists
            )

            return render_template('fetch_data.html', playlist_options=playlist_options)

        except requests.exceptions.RequestException as e:
            print(f"❌ API Error: {e}")
            return f'<h1>Error:</h1><p>Failed to fetch playlists: {e}</p><p><a href="/">Go back home</a></p>'
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return f'<h1>Error:</h1><p>Unexpected error: {e}</p><p><a href="/">Go back home</a></p>'

@app.route('/download/<filename>')
def download_file(filename):
    """Serve the JSON file for download"""
    file_path = os.path.join(os.getcwd(), filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return '<h1>Error:</h1><p>File not found.</p>'

@app.route('/oauth/callback')
def oauth_callback():
    # Simulate token extraction logic here
    # token = extract_token_logic()
    return render_template('loading.html')

@app.after_request
def redirect_to_dashboard(response):
    if response.status_code == 200 and request.path == '/oauth/callback':
        return redirect('/dashboard')
    return response

@app.route('/dashboard')
def dashboard():
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/login')

    if 'user_name' in session and 'user_id' in session:
        user_name = session['user_name']
        user_id = session['user_id']
    else:
        try:
            user_data = make_spotify_request('/me', access_token)
            user_name = user_data.get('display_name', 'User')
            user_id = user_data.get('id')
            session['user_name'] = user_name  # Store user name in session
            session['user_id'] = user_id  # Store user ID in session
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user data: {e}")
            return '<h1>Error:</h1><p>Failed to fetch user data. Please <a href="/login">login</a> again.</p>'

    return render_template('dashboard.html', user_name=user_name)

@app.route('/logout')
def logout():
    """Logout and clear the session"""
    session.clear()
    return redirect('/')

@app.route('/extract-playlists')
def extract_playlists():
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/login')

    if 'playlists' in session:
        playlists = session['playlists']
    else:
        try:
            user_id = session.get('user_id')
            if not user_id:
                user_data = make_spotify_request('/me', access_token)
                user_id = user_data.get('id')
                session['user_id'] = user_id

            playlists = fetch_all_playlists(access_token, user_id)
            session['playlists'] = playlists  # Cache playlists in session
        except requests.exceptions.RequestException as e:
            print(f"Error fetching playlists: {e}")
            return '<h1>Error:</h1><p>Failed to fetch playlists. Please <a href="/login">login</a> again.</p>'

    return render_template('extracting_playlists.html', playlists=playlists)

@app.route('/set-selected-playlists', methods=['POST'])
def set_selected_playlists():
    """Store selected playlists in the session"""
    selected_playlists = request.json.get('playlists', [])
    session['selected_playlists'] = selected_playlists
    return '', 204

@app.route('/extract-tracks')
def extract_tracks():
    """Render the extract tracks page and handle track extraction asynchronously"""
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/login')

    selected_playlists = session.get('selected_playlists', [])
    if not selected_playlists:
        return '<h1>Error:</h1><p>No playlists selected. Please go back and select at least one playlist.</p>'

    # Render the extract_tracks.html page
    return render_template('extract_tracks.html')

if __name__ == '__main__':
    PORT = 8080
    # Check if environment variables are set
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print(".env variables SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not configured correctly")
        exit(1)
    
    print("Starting Spotify Playlist Ripper...")
    print(f"Server running at: http://127.0.0.1:{PORT}")
    
    app.run(host='127.0.0.1', port=PORT, debug=True)