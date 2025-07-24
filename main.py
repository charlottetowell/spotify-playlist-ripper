import os
import secrets
import requests
from flask import Flask, request, redirect, session
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
SCOPES = 'playlist-read-private playlist-read-collaborative'

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
        <a href="/">Go back home</a>
        '''
        
    except requests.exceptions.RequestException as e:
        print(f"Error exchanging code for token: {e}")
        return f'<h1>Error:</h1><p>Failed to exchange code for token: {e}</p>'

if __name__ == '__main__':
    PORT = 8080
    # Check if environment variables are set
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print(".env variables SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not configured correctly")
        exit(1)
    
    print("Starting Spotify Playlist Ripper...")
    print(f"Server running at: http://127.0.0.1:{PORT}")
    
    app.run(host='127.0.0.1', port=PORT, debug=True)