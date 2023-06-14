from flask import Flask, render_template, request, url_for, redirect  # , session
import openai
import joblib
import json
import spotipy.util as util
import random
from moodtape_functions import authenticate_spotify, aggregate_top_artists, aggregate_top_tracks, select_tracks, create_playlist
from supabase import create_client, Client


supabase_url = "https://adhqbycntsyljqyknkzk.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFkaHFieWNudHN5bGpxeWtua3prIiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODY2NTI1MzYsImV4cCI6MjAwMjIyODUzNn0.FLzYbKMCmBmdZNPqwSfKOSKLg50iZt0dkGM4dr128Zg"
client_id = 'fe950c4faf544e42af36cfa40473ccd3'
client_secret = 'c37d08196f3644a081b8dd97854e2be7'
redirect_uri = 'http://localhost:8000/callback'
scope = 'user-library-read user-top-read playlist-modify-public user-follow-read'
supabase: Client = create_client(supabase_url, supabase_key)
openai.api_key = ""
global chat
chat = ''
global selected_tracks
selected_tracks = []
global username
username = ''
messages = [{'role': 'system',
             'content': 'Act as a chat bot that asks questions to understand the mood of the user and reply accordingly. if the user deviates and asks other questions not related to their mood, bring the user back to this. Keep the converstion only until the mood is clear or the user seems done chatting.'}]

app = Flask(__name__)
# app.secret_key = 'secret_key'
# app.config['SESSION_TYPE'] = 'filesystem'


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/input', methods=['GET', 'POST'])
def my_form():
    if request.method == 'POST':
        global username
        username = request.form['username']
        return redirect(url_for('chatbot'))
    return render_template('input.html')


@app.route("/chat", methods=["GET"])
def chatbot():
    return render_template("chatbot.html")


@app.route("/api", methods=["POST"])
def api():
    global chat
    message = request.json.get("message")
    chat = chat+' ' + message
    mess = {'role': 'user', 'content': message}
    messages.append(mess)
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    print(chat)
    if completion.choices[0].message != None:
        messages.append(dict(completion.choices[0].message))
        return completion.choices[0].message
    else:
        return 'Failed to Generate response!'


@app.route("/songs", methods=['POST'])
def moodtape():
    global username
    playlist_option = bool(request.form.get('create_playlist'))
    # load trained model and countvectorizer
    mnb_model, cv = joblib.load(
        open("Emotunes_nb_cv.pkl", "rb"))
    #chat = ['I am happy because i won a dance competition yesterday']
    mood = mnb_model.predict(cv.transform([chat]))
    print('mood', mood[0])
    print('user', username)

    data = supabase.table("emo_table").insert(
        {"Username": username, "mood": mood[0]}).execute()
    assert len(data.data) > 0

    token = util.prompt_for_user_token(username,
                                       scope=scope,
                                       client_id=client_id,
                                       client_secret=client_secret,
                                       redirect_uri=redirect_uri)
    spotify_auth = authenticate_spotify(token)
    global top_artists_names
    top_artists_uri, top_artists_names = aggregate_top_artists(spotify_auth)
    print(top_artists_names)
    top_tracks = aggregate_top_tracks(spotify_auth, top_artists_uri)
    global selected_tracks
    selected_tracks = select_tracks(spotify_auth, top_tracks, mood)

    random.shuffle(selected_tracks)
    selected_tracks = selected_tracks[:25]
    global playlist
    if playlist_option:
        playlist = create_playlist(spotify_auth, selected_tracks, mood)
        print(playlist)
    else:
        playlist = None
    print('final', selected_tracks)
    return redirect(url_for('display_tracks', page=1))


@app.route('/songs/<int:page>')
def display_tracks(page):
    global playlist
    print(page)
    track_ids = selected_tracks
    tracks_per_page = 1
    start_index = (page - 1) * tracks_per_page
    end_index = start_index + tracks_per_page
    tracks = track_ids[start_index:end_index]
    print(tracks)
    return render_template('songs.html', track_ids=tracks, page=page, tracks_per_page=tracks_per_page, total=len(selected_tracks), playlist=playlist)


@app.route("/profile", methods=["GET"])
def profile():
    global top_artists_names
    global username
    print('topa:', top_artists_names)
    print('user', username)
    data = supabase.table('emo_table').select('mood').eq(
        'Username', username).execute()
    print('resp:', data.data)
    if data:
        moods = [record['mood'] for record in data.data]
        mood_counts = {}
        for mood in moods:
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
        labels = list(mood_counts.keys())
        values = list(mood_counts.values())
        chart_data = json.dumps({'labels': labels, 'values': values})
    else:
        print("No data found")
    return render_template("profile.html", chart_data=chart_data, artists=top_artists_names[:5], username=username)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8000)
