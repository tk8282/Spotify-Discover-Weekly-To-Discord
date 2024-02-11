from discord import Webhook
from discord import SyncWebhook
from dotenv import load_dotenv
import os
import base64
from requests import post
import requests
import json
from datetime import datetime, timedelta

# load environment variable file (holds client id, secret, and refresh token)
load_dotenv()

# gets id, secret, and refresh token
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
refresh_token = os.getenv("REFRESH_TOKEN")

# gets the current access token or refreshes it if expired
def get_token():
    global refresh_token  # use the global refresh_token variable
    current_time = datetime.now()
    
    # check if the token is present and not expired
    if refresh_token and 'token_expiration' in globals() and current_time < token_expiration:
        return os.getenv("ACCESS_TOKEN")  # return the current access token

    # concat id and secret then encode it in base64
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    # endpoint of Spotify OAuth service that I am sending request to
    url = "https://accounts.spotify.com/api/token"
    
    # headers
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # data needed to be passed
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

    # post request
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)

    # parse token
    new_token = json_result.get("access_token")
    refresh_token = json_result.get("refresh_token") or refresh_token  # keep the current refresh token if not returned
    expiration_seconds = json_result.get("expires_in") or 3600  # set default expiration to 1 hour

    # calculate expiration time
    token_expiration = current_time + timedelta(seconds=expiration_seconds)

    # store new token and refresh token in .env file
    os.environ["ACCESS_TOKEN"] = new_token
    os.environ["REFRESH_TOKEN"] = refresh_token
    os.environ["TOKEN_EXPIRATION"] = token_expiration.strftime("%Y-%m-%dT%H:%M:%S")

    return new_token

# easier way to construct header for future requests
def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

# gets the name, artists, and link to the song of a specific playlist
def get_discover_weekly_tracks():
    # Hardcoded playlist ID for "Discover Weekly"
    discover_weekly_playlist_id = "37i9dQZEVXcNBg9cq7OOWJ"

    # Print debug information
    print(f"Playlist ID: {discover_weekly_playlist_id}")

    # Define the Spotify API endpoint for getting playlist tracks
    endpoint = f'https://api.spotify.com/v1/playlists/{discover_weekly_playlist_id}/tracks'

    # Set up headers with the access token for authentication
    headers = get_auth_header(token)

    # Make a GET request to the Spotify API
    response = requests.get(endpoint, headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Extract information about each track from the response
        tracks_info = response.json().get('items', [])

        # Extract the names of songs, their artists, and the link to each song
        song_info = [
            (
                track['track']['name'],
                ', '.join(artist['name'] for artist in track['track']['artists']),
                track['track']['external_urls']['spotify']
            )
            for track in tracks_info
        ]

        return song_info
    else:
        # If the request was not successful, print an error message and response
        print(f"Error: {response.status_code}")
        print(response.headers)  # Print headers for debugging
        print(response.content)  # Print content for debugging
        return None

# Create a Discord webhook object
webhook_url = "https://discord.com/api/webhooks/1206121720994340924/a9V7C4-MqZrVHZWdtrZFmgrOzYp-c5r78rmrgRNyjbddXvwXvB9Imex5tVt-dnToMCS_"
webhook = SyncWebhook.from_url(webhook_url)

# Example usage of the function
token = get_token()

# Print debug information
print(f"Access Token: {token}")

discover_weekly_tracks = get_discover_weekly_tracks()

if discover_weekly_tracks:
    #gets current date
    current_date = datetime.now().strftime("%Y-%m-%d")

    #Sends the current date of the program being run
    message_header = f"New Discover Weekly Songs on {current_date}:\n ***VOLUME WARNING*** DON'T LISTEN IN THE DISCORD PREVIEW"
    webhook.send(message_header)

    #gets the amount of songs in the playlist
    total_songs = len(discover_weekly_tracks)

    for i, (song, artists, link) in enumerate(discover_weekly_tracks, start=1):
        #create string for each message
        message = f"```markdown\nSong {i}/{total_songs}: {song}\nArtist: {artists}\n```\nLink: {link}"

        #send message
        webhook.send(message)

    print("All Discover Weekly tracks sent.")
else:
    print("Failed to retrieve Discover Weekly tracks.")