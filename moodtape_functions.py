import spotipy
import spotipy.util as util

import random


def authenticate_spotify(token):
    print('...connecting to Spotify')
    sp = spotipy.Spotify(auth=token)
    return sp

# Step 2. Creating a list of your favorite artists


def aggregate_top_artists(sp):
    print('...getting your top artists')
    top_artists_name = []
    top_artists_uri = []

    ranges = ['short_term', 'medium_term', 'long_term']
    for r in ranges:
        top_artists_all_data = sp.current_user_top_artists(
            limit=5, time_range=r)
        top_artists_data = top_artists_all_data['items']
        for artist_data in top_artists_data:
            if artist_data["name"] not in top_artists_name:
                top_artists_name.append(artist_data['name'])
                top_artists_uri.append(artist_data['uri'])

    followed_artists_all_data = sp.current_user_followed_artists(limit=5)
    followed_artists_data = (followed_artists_all_data['artists'])
    for artist_data in followed_artists_data["items"]:
        if artist_data["name"] not in top_artists_name:
            top_artists_name.append(artist_data['name'])
            top_artists_uri.append(artist_data['uri'])
    return top_artists_uri, top_artists_name


# Step 3. For each of the artists, get a set of tracks for each artist

def aggregate_top_tracks(sp, top_artists_uri):
    print("...getting top tracks")
    top_tracks_uri = []
    for artist in top_artists_uri:
        top_tracks_all_data = sp.artist_top_tracks(artist)
        top_tracks_data = top_tracks_all_data['tracks']
        for track_data in top_tracks_data:
            top_tracks_uri.append(track_data['uri'])
    results = sp.current_user_saved_tracks()
    track_uris = [item["track"]["uri"] for item in results["items"]]
    top_tracks_uri.extend(track_uris)
    print('liked', track_uris)
    return top_tracks_uri

# Step 4. From top tracks, select tracks that are within a certain mood range


def select_tracks(sp, top_tracks_uri, mood):
    print("...selecting tracks")
    selected_tracks_uri = []
    if mood == 'joy':
        playlist_id = "37i9dQZF1EVJSvZp5AOML2"
        results = sp.playlist_tracks(playlist_id)
        for track in results["items"][:10]:
            selected_tracks_uri.append(track["track"]["uri"])
    elif mood == 'sadness':
        playlist_id = "37i9dQZF1EIdChYeHNDfK5"
        results = sp.playlist_tracks(playlist_id)
        for track in results["items"][:10]:
            selected_tracks_uri.append(track["track"]["uri"])
    elif mood == 'anger':
        playlist_id = "37i9dQZF1EIgNZCaOGb0Mi"
        results = sp.playlist_tracks(playlist_id)
        for track in results["items"][:10]:
            selected_tracks_uri.append(track["track"]["uri"])
    elif mood == 'surprise':
        playlist_id = "2qVmU4fTWzDZ3qAbylWpAQ"
        results = sp.playlist_tracks(playlist_id)
        for track in results["items"][0:]:
            selected_tracks_uri.append(track["track"]["uri"])
    elif mood == 'love':
        playlist_id = "37i9dQZF1EIgnXj6uD4zub"
        results = sp.playlist_tracks(playlist_id)
        for track in results["items"][:10]:
            selected_tracks_uri.append(track["track"]["uri"])
    print(selected_tracks_uri)

    def group(seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    random.shuffle(top_tracks_uri)
    for tracks in list(group(top_tracks_uri, 50)):
        tracks_all_data = sp.audio_features(tracks)
        for track_data in tracks_all_data:
            try:
                if mood == 'joy':
                    if (0.75 <= track_data["valence"] <= 1
                        and track_data["danceability"] >= 0.5
                            and 0.5 <= track_data["energy"] <= 1):
                        selected_tracks_uri.append(track_data["uri"])
                elif mood == 'love':
                    if (0.75 <= track_data["valence"] <= 1
                        and track_data["danceability"] <= 0.75
                            and 0 <= track_data["energy"] <= 0.5):
                        selected_tracks_uri.append(track_data["uri"])
                elif mood == 'sadness':
                    if (0 <= track_data["valence"] <= 0.5
                            and 0 <= track_data["danceability"] <= 0.5
                            and 0 <= track_data["energy"] <= 0.5):
                        selected_tracks_uri.append(track_data["uri"])
                        playlist_id = "37i9dQZF1EVJSvZp5AOML2"
                        results = sp.playlist_tracks(playlist_id)
                        for track in results["items"][:10]:
                            selected_tracks_uri.append(track["track"]["uri"])
                elif mood == 'anger':
                    if (0 <= track_data["valence"] <= 0.5
                            and track_data["danceability"] >= 0.5
                            and 0.75 <= track_data["energy"] <= 1):
                        selected_tracks_uri.append(track_data["uri"])
                        playlist_id = "37i9dQZF1EVJSvZp5AOML2"
                        results = sp.playlist_tracks(playlist_id)
                        for track in results["items"][:10]:
                            selected_tracks_uri.append(track["track"]["uri"])
                elif mood == 'fear':
                    if (0 <= track_data["valence"] <= 0.5
                            and track_data["danceability"] <= 0.5
                            and 0.5 <= track_data["energy"] <= 1):
                        selected_tracks_uri.append(track_data["uri"])
                        playlist_id = "37i9dQZF1EVJSvZp5AOML2"
                        results = sp.playlist_tracks(playlist_id)
                        for track in results["items"][:10]:
                            selected_tracks_uri.append(track["track"]["uri"])

            except TypeError as te:
                continue
    return selected_tracks_uri

# Step 5. From these tracks, create a playlist for user


def create_playlist(sp, selected_tracks_uri, mood):

    print("...creating playlist")
    user_all_data = sp.current_user()
    user_id = user_all_data["id"]

    playlist_all_data = sp.user_playlist_create(
        user_id, 'Emotunes_'+str(mood[0]))
    playlist_id = playlist_all_data["id"]
    playlist_uri = playlist_all_data["uri"]

    # random.shuffle(selected_tracks_uri)
    # try:
    sp.user_playlist_add_tracks(
        user_id, playlist_id, selected_tracks_uri[0:])
    # except spotipy.client.SpotifyException as s:
    # 	print("could not add tracks")

    return playlist_uri

# spotify_auth = authenticate_spotify()
# top_artists = aggregate_top_artists(spotify_auth)
# top_tracks = aggregate_top_tracks(spotify_auth, top_artists)
# selected_tracks = select_tracks(spotify_auth, top_tracks)
# create_playlist(spotify_auth, selected_tracks)
