from flask import Flask, render_template_string, request, redirect, url_for, jsonify, session
import os
import requests
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "skibiditoilet"  # Change this to your desired secret key

# Spotify Credentials
SPOTIFY_CLIENT_ID = "4d39193783154379856697239f291d2f"
SPOTIFY_CLIENT_SECRET = "2085a538d78c4df39f854c3750b5f666"

# Database setup
def init_db():
    with sqlite3.connect("messages.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient TEXT,
                message TEXT,
                spotify_url TEXT,
                album_image TEXT,
                track_name TEXT,
                artist_name TEXT
            )
        """)
    conn.close()

init_db()

def get_spotify_token():
    """Obtain an access token using the Client Credentials Flow (no user login required)."""
    token_url = "https://accounts.spotify.com/api/token"
    response = requests.post(token_url, data={
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    })
    response_data = response.json()
    session['spotify_token'] = response_data.get("access_token")

# HTML Templates
index_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Send the Song</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <style>
        body {
            font-family: 'Montserrat', sans-serif;
            background-color: #e9ecef;
            color: #343a40;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }
        .container {
            max-width: 600px;
            width: 100%;
            padding: 20px;
            text-align: center;
            margin-top: 20px;
            background: #ffffff;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        h1 {
            margin-bottom: 20px;
            font-size: 2.5em;
            font-family: 'Playfair Display', serif;
            color: #1DB954;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
        }
        button {
            background-color: #1DB954;
            color: #fff;
            padding: 12px;
            width: 100%;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
            transition: background-color 0.3s;
            font-size: 1.1em;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        }
        button:hover {
            background-color: #17a648;
            transform: translateY(-2px);
        }
        .slider {
            width: 100%;
            overflow: hidden;
            margin-top: 20px;
            position: relative;
        }
        .slider-container {
            display: flex;
            animation: scroll 15s linear infinite;  /* Faster scrolling */
        }
        .card {
            min-width: 300px;
            margin: 10px;
            background: #ffffff;
            border-radius: 8px;
            padding: 15px;
            text-align: left;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s;
            position: relative;
            overflow: hidden;
            border: 2px solid #1DB954; /* Green border */
        }
        .card:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        }
        .card-title {
            font-size: 1.2em;
            color: #333;
            font-weight: bold;
        }
        .card-message {
            font-size: 0.9em;
            color: #555;
            margin: 5px 0;
        }
        .album-image {
            width: 50px;
            height: 50px;
            border-radius: 5px;
            margin-right: 10px;
            vertical-align: middle;
        }
        .track-info {
            display: flex;
            align-items: center;
            margin-top: 5px;
        }
        @keyframes scroll {
            0% { transform: translateX(0); }
            100% { transform: translateX(-50%); }
        }
        .vintage-popup {
            border: 3px solid #b2967d;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        .vintage-popup .swal2-timer-progress-bar {
            background-color: #b2967d;
        }
        .swal2-title {
            font-family: 'Georgia', serif;
            font-size: 24px;
            color: #3a2f2f;
            text-shadow: 1px 1px 2px #b2967d;
        }
        .swal2-html-container {
            font-family: 'Courier New', monospace;
            color: #5a4b3e;
            line-height: 1.5;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Send the Song</h1>
        <button onclick="confirmRedirect('send_song')">Send the Song</button>
        <button onclick="confirmRedirect('browse')">Browse Messages</button>
    </div>

    <div class="slider">
        <div class="slider-container" id="sliderContainer">
            {% for msg in messages %}
                <div class="card" onclick="window.location.href='/message/{{ msg[0] }}'">
                    <p class="card-title"><strong>To:</strong> {{ msg[1] }}</p>
                    <p class="card-message">{{ msg[2] }}</p>
                    {% if msg[4] %}
                        <div class="track-info">
                            <img src="{{ msg[4] }}" class="album-image" alt="Album Image">
                            <span>{{ msg[5] }} - {{ msg[6] }}</span>
                        </div>
                    {% endif %}
                </div>
            {% endfor %}
        </div>
    </div>

    <script>
        function confirmRedirect(route) {
            Swal.fire({
                title: '✨ Redirecting...',
                html: '<p style="font-family: Georgia, serif; font-size: 18px; color: #3a2f2f;">You will be redirected in <b>3</b> seconds...</p>',
                timer: 3000,
                timerProgressBar: true,
                background: '#f9f2e7',
                color: '#3a2f2f',
                showCancelButton: false,
                showConfirmButton: false,
                width: '450px',
                padding: '2rem',
                customClass: {
                    popup: 'vintage-popup',
                },
                willOpen: () => {
                    const b = Swal.getHtmlContainer().querySelector('b');
                    let secondsLeft = 3;
                    const timerInterval = setInterval(() => {
                        secondsLeft -= 1;
                        b.textContent = secondsLeft;
                    }, 1000);

                    Swal.showLoading();
                },
                onClose: () => {
                    clearInterval(timerInterval);
                }
            }).then((result) => {
                if (result.dismiss === Swal.DismissReason.timer) {
                    window.location.href = `/${route}`;
                }
            });
        }
    </script>
</body>
</html>
"""

send_song_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Send The Song</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400; 700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Montserrat', sans-serif;
            background-color: #f8f9fa;
            color: #343a40;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            max-width: 600px;
            width: 100%;
            padding: 20px;
            text-align: center;
            background: #ffffff;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        h1 {
            margin-bottom: 20px;
            font-size: 2.5em;
            font-family: 'Playfair Display', serif;
            color: #1DB954;
        }
        .form-container {
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        form label {
            display: block;
            margin: 10px 0 5px;
            color: #555;
        }
        form input, form textarea {
            width: 100%;
            padding: 12px;
            background: #f0f0f0;
            color: #333;
            border: 1px solid #ccc;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        form button {
            background-color: #1DB954;
            color: #fff;
            padding: 12px;
            width: 100%;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        form button:hover {
            background-color: #17a648;
        }
        #songSuggestions {
            background: #f0f0f0;
            border-radius: 4px;
            max-height: 150px;
            overflow-y: auto;
            display: none;
        }
        #songSuggestions div {
            padding: 10px;
            cursor: pointer;
            color: #555;
        }
        #songSuggestions div:hover {
            background: #ddd;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Send The Song</h1>
        <div class="form-container">
            <form action="{{ url_for('submit') }}" method="POST">
                <label for="to"> To:</label>
                <input type="text" name="to" id="to" placeholder="Recipient's name" required>

                <label for="message">Message:</label>
                <textarea name="message" id="message" placeholder="Write your message..." required></textarea>

                <label for="spotify_url">Song:</label>
                <input type="text" id="song_search" placeholder="Search for a song" oninput="searchSpotifySongs(this.value)">
                <div id="songSuggestions"></div>
                <input type="hidden" name="spotify_url" id="spotify_url">
                <input type="hidden" name="album_image" id="album_image">
                <input type="hidden" name="track_name" id="track_name">
                <input type="hidden" name="artist_name" id="artist_name">

                <button type="submit">Submit Message</button>
            </form>
        </div>
    </div>

    <script>
        async function searchSpotifySongs(query) {
            if (query.length < 3) return;
            const response = await fetch('/search_song?query=' + encodeURIComponent(query));
            const results = await response.json();
            const suggestions = document.getElementById("songSuggestions");
            suggestions.innerHTML = "";
            if (results.tracks.items) {
                results.tracks.items.forEach(track => {
                    const item = document.createElement("div");
                    item.textContent = track.name + " - " + track.artists.map(artist => artist.name).join(", ");
                    const tracksImage = document.createElement("img");
                    tracksImage.src = track.album.images[0].url;  // Get the album image
                    tracksImage.className = "album-image"; // Set class for styling
                    item.prepend(tracksImage);
                    item.onclick = () => {
                        document.getElementById("spotify_url").value = track.external_urls.spotify;
                        document.getElementById("album_image").value = track.album.images[0].url; // Save album image URL
                        document.getElementById("track_name").value = track.name; // Save track name
                        document.getElementById("artist_name").value = track.artists.map(artist => artist.name).join(", "); // Save artist names
                        document.getElementById("song_search").value = track.name + " - " + track.artists.map(artist => artist.name).join(", ");
                        suggestions.style.display = "none";
                    };
                    suggestions.appendChild(item);
                });
                suggestions.style.display = "block";
            }
        }
    </script>
</body>
</html>
"""

browse_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Browse Messages</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Montserrat', sans-serif;
            background-color: #e9ecef;
            color: #343a40;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            max-width: 600px;
            width: 100%;
            padding: 20px;
            text-align: center;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        h1 {
            margin-bottom: 20px;
            font-size: 2.5em;
            font-family: 'Playfair Display', serif;
            color: #1DB954;
        }
        form label {
            display: block;
            margin: 15px 0 5px;
            color: #555;
        }
        form input {
            width: 100%;
            padding: 12px;
            background: #f0f0f0;
            color: #333;
            border: 1px solid #ccc;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        form button {
            background-color: #1DB954;
            color: #fff;
            padding: 12px;
            width: 100%;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        form button:hover {
            background-color: #17a648;
        }
        .message {
            margin: 20px 0;
            background: #fff;
            padding: 15px;
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.3s;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        }
        .message:hover {
            transform: scale(1.02);
        }
        .message p {
            margin: 5px 0;
            color: #555;
        }
        .message .track-info {
            display: flex;
            align-items: center;
            margin-top: 5px;
        }
        .album-image {
            width: 50px;
            height: 50px;
            border-radius: 5px;
            margin-right: 10px;
        }
        .message iframe {
            width: 100%;
            height: 200px; /* Increased height for better visibility */
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Browse Messages</h1>
        <form action="{{ url_for('browse') }}" method="GET">
            <label for="recipient">Recipient's Name:</label>
            <input type="text" name="recipient" required>
            <button type="submit">Search</button>
        </form>

        <div id="messages">
            {% if messages %}
                {% for msg in messages %}
                    <div class="message" onclick="window.location.href='/message/{{ msg[0] }}'">
                        <p><strong>To:</strong> {{ msg[1] }}</p>
                        <p>{{ msg[2] }}</p>
                        {% if msg[4] %}
                            <div class="track-info">
                                <img src="{{ msg[4] }}" class="album-image" alt="Album Image">
                                <span>{{ msg[5] }} - {{ msg[6] }}</span>
                            </div>
                        {% endif %}
                    </div>
                {% endfor %}
            {% else %}
                <p>No messages found.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

message_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Message Details</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Montserrat', sans-serif;
            background-color: #e9ecef;
            color: #343a40;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            max-width: 600px;
            width: 100%;
            padding: 20px;
            text-align: center;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        h1 {
            margin-bottom: 20px;
            font-size: 2.5em;
            font-family: 'Playfair Display', serif;
            color: #1DB954;
        }
        .message {
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        }
        .message p {
            margin: 5px 0;
            color: #555;
        }
        .message .track-info {
            display: flex;
            align-items: center;
            margin-top: 5px;
        }
        .album-image {
            width: 50px;
            height: 50px;
            border-radius: 5px;
            margin-right: 10px;
        }
        .message iframe {
            width: 100%;
            height: 300px; /* Increased height for better visibility */
            border-radius: 8px;
        }
        button {
            background-color: #1DB954;
            color: #fff;
            padding: 12px;
            width: 100%;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #17a648;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Message Details</h1>
        <div class="message">
            <p><strong>To:</strong> {{ recipient }}</p>
            <p><strong>Message:</strong> {{ message }}</p>
            {% if spotify_url %}
                <iframe src="{{ spotify_url.replace('open.spotify.com', 'embed.spotify.com') }}" frameborder="0" allow="encrypted-media"></iframe>
            {% endif %}
        </div>
        <button onclick="window.location.href='/'">Back to Home</button>
    </div>
</body>
</html>
"""

@app.route('/message/<int:message_id>')
def message_details(message_id):
    with sqlite3.connect("messages.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT recipient, message, spotify_url, album_image, track_name, artist_name FROM messages WHERE id = ?", (message_id,))
        message = cursor.fetchone()
    if message:
        return render_template_string(message_template, recipient=message[0], message=message[1], spotify_url=message[2], album_image=message[3], track_name=message[4], artist_name=message[5])
    return "Message not found", 404

@app.route('/')
def index():
    messages = []
    # Load messages from the database to display in the slider
    with sqlite3.connect("messages.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, recipient, message, spotify_url, album_image, track_name, artist_name FROM messages")
        messages = cursor.fetchall()
    random.shuffle(messages)  # Shuffle messages for random display
    return render_template_string(index_template, messages=messages)

@app.route('/send_song')
def send_song():
    if 'spotify_token' not in session:
        get_spotify_token()
    return render_template_string(send_song_template)

@app.route('/submit', methods=['POST'])
def submit():
    recipient = request.form.get("to")
    message = request.form.get("message")
    spotify_url = request.form.get("spotify_url")
    album_image = request.form.get("album_image")
    track_name = request.form.get("track_name")
    artist_name = request.form.get("artist_name")

    with sqlite3.connect("messages.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (recipient, message, spotify_url, album_image, track_name, artist_name) VALUES (?, ?, ?, ?, ?, ?)",
                       (recipient, message, spotify_url, album_image, track_name, artist_name))
        message_id = cursor.lastrowid  # Get the ID of the newly inserted message
    return redirect(url_for('message_details', message_id=message_id))  # Redirect to the message details page

@app.route('/browse', methods=['GET'])
def browse():
    recipient = request.args.get("recipient")
    messages = []  # Initialize messages as an empty list
    with sqlite3.connect("messages.db") as conn:
        cursor = conn.cursor()
        if recipient:
            cursor.execute("SELECT id, recipient, message, spotify_url, album_image, track_name, artist_name FROM messages WHERE recipient LIKE ?", ('%' + recipient + '%',))
            messages = cursor.fetchall()
    return render_template_string(browse_template, messages=messages)

@app.route('/search_song')
def search_song():
    query = request.args.get('query')
    if query:
        if 'spotify_token' not in session:
            get_spotify_token()

        headers = {
            'Authorization': f'Bearer {session.get("spotify_token")}'
        }
        response = requests.get(f'https://api.spotify.com/v1/search?q={query}&type=track', headers=headers)
        return jsonify(response.json())
    return jsonify({"error": "No query provided"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
