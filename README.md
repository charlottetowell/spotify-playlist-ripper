# Spotify Playlist Ripper

A Flask app that authorises with Spotify's web API to extract your playlist & track information into a downloadable JSON file.

**Why?** Because it beats waiting "up to 30 days" for Spotify to email you a bulk data export of your account [🔗](https://support.spotify.com/au/article/understanding-my-data/)

**Contents:**
* [Demo](#demo)
* [How to Run Locally](#running-locally)

## Demo

![Home Page Screenshot](/screenshots/HomePage.png)
![Sup User Screenshot](/screenshots/SupUser.png)
![Playlist Selector Screenshot](/screenshots/PlaylistSelector.png)
![Tracks Extracted Screenshot](/screenshots/TracksExtracted.png)

## Running Locally


1. Install dependencies via `  pip install -r requirements.txt`

2. Create a developer app in Spotify - see [Spotify Docs Here](https://developer.spotify.com/documentation/web-api/tutorials/getting-started)

3. Add the following redirect URI: `127.0.0.1:8080/oauth/callback`

4. Populate .env with your own variables from Spotify   

5. Run the server locally via `python main.py`

The server will start at `http://127.0.0.1:8080`