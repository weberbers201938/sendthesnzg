from flask import Flask, render_template_string, request, redirect, url_for, jsonify, session
import os
import requests
import sqlite3

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
                spotify_url TEXT
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
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <style>
        body { font-family: Arial, sans-serif; background-color: #121212; color: #f2f2f2; display: flex; flex-direction: column; align-items: center; height: 100vh; margin: 0; }
        .container { max-width: 500px; width: 100%; padding: 20px; text-align: center; }
        button { background-color: #1DB954; color: #fff; padding: 12px; width: 100%; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #17a648; }
        .slider { width: 100%; overflow: hidden; position: relative; }
        .slider-container { display: flex; animation: slide 20s linear infinite; }
        .card { min-width: 300px; margin: 10px; background: #1f1f1f; border-radius: 8px; padding: 15px; }
        .card img { width: 100%; height: auto; border-radius: 8px; }
        .card iframe { width: 100%; height: 80px; border-radius: 8px; }

        @keyframes slide {
            0% { transform: translateX(0); }
            20% { transform: translateX(0); }
            25% { transform: translateX(-100%); }
            45% { transform: translateX(-100%); }
            50% { transform: translateX(-200%); }
            70% { transform: translateX(-200%); }
            75% { transform: translateX(-300%); }
            100% { transform: translateX(-300%); }
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
                <div class="card">
                    <p><strong>To:</strong> {{ msg[0] }}</p>
                    <p>{{ msg[1] }}</p>
                    {% if msg[2] %}
                        <iframe src="{{ msg[2].replace('open.spotify.com', 'embed.spotify.com') }}" frameborder="0" allow="encrypted-media"></iframe>
                    {% endif %}
                </div>
            {% endfor %}
            <!-- Duplicate the cards for infinite effect -->
            {% for msg in messages %}
                <div class="card">
                    <p><strong>To:</strong> {{ msg[0] }}</p>
                    <p>{{ msg[1] }}</p>
                    {% if msg[2] %}
                        <iframe src="{{ msg[2].replace('open.spotify.com', 'embed.spotify.com') }}" frameborder="0" allow="encrypted-media"></iframe>
                    {% endif %}
                </div>
            {% endfor %}
        </div>
    </div>

    <script>
        function confirmRedirect(route) {
            Swal.fire({
                title: 'Redirecting...',
                text: 'You will be redirected in 3 seconds.',
                timer: 3000,
                timerProgressBar: true,
                showCancelButton: false,
                showConfirmButton: false,
                willOpen: () => {
                    Swal.showLoading()
                },
                onClose: () => {
                    clearInterval(timerInterval)
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
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <style>
        body { font-family: Arial, sans-serif; background-color: #121212; color: #f2f2f2; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { max-width: 500px; width: 100%; padding: 20px; text-align: center; }
        .form-container { background: #1f1f1f; padding: 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); margin-bottom: 20px; }
        form label { display: block; margin: 10px 0 5px; color: #bbb; }
        form input, form textarea { width: 100%; padding: 12px; background: #333; color: #fff; border: 1px solid #555; border-radius: 4px; }
        form button { background-color: #1DB954; color: #fff; padding: 12px; width: 100%; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        form button:hover { background-color: #17a648; }
        #songSuggestions { background: #333; border-radius: 4px; max-height: 150px; overflow-y: auto; display: none; }
        #songSuggestions div { padding: 10px; cursor: pointer; color: #bbb; }
        #songSuggestions div:hover { background: #444; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Send The Song</h1>
        <div class="form-container">
            <form action="{{ url_for('submit') }}" method="POST">
                <label for="to">To:</label>
                <input type="text" name="to" id="to" placeholder="Recipient's name" required>

                <label for="message">Message:</label>
                <textarea name="message" id="message" placeholder="Write your message..." required></textarea>

                <label for="spotify_url">Song:</label>
                <input type="text" id="song_search" placeholder="Search for a song" oninput="searchSpotifySongs(this.value)">
                <div id="songSuggestions"></div>
                <input type="hidden" name="spotify_url" id="spotify_url">

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
                    const albumImage = document.createElement("img");
                    albumImage.src = track.album.images[0].url; // Get the album image
                    albumImage.style.width = "50px"; // Set a width for the image
                    albumImage.style.marginRight = "10px"; // Add some margin
                    item.prepend(albumImage); // Add the image to the suggestion item
                    item.onclick = () => {
                        document.getElementById("spotify_url").value = track.external_urls.spotify;
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
    <style>
        body { font-family: Arial, sans-serif; background-color: #121212; color: #f2f2f2; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { max-width: 600px; width: 100%; padding: 20px; text-align: center; background-color: #1f1f1f; border-radius: 8px; }
        form label { display: block; margin: 15px 0 5px; color: #bbb; }
        form input { width: 100%; padding: 12px; background: #333; color: #fff; border: 1px solid #555; border-radius: 4px; margin-bottom: 15px; }
        form button { background-color: #1DB954; color: #fff; padding: 12px; width: 100%; border: none; border-radius: 4px; cursor: pointer; }
        form button:hover { background-color: #17a648; }
        .message { margin: 20px 0; background: #333; padding: 15px; border-radius: 8px; }
        .message p { margin: 5px 0; color: #bbb; }
        .message iframe { width: 100%; height: 80px; border-radius: 8px; }
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
                    <div class="message">
                        <p><strong>To:</strong> {{ msg[0] }}</p>
                        <p>{{ msg[1] }}</p>
                        {% if msg[2] %}
                            <iframe src="{{ msg[2].replace('open.spotify.com', 'embed.spotify.com') }}" frameborder="0" allow="encrypted-media"></iframe>
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

@app.route('/')
def index():
    messages = []  # Load messages from the database to display in the slider
    with sqlite3.connect("messages.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT recipient, message, spotify_url FROM messages")
        messages = cursor.fetchall()
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

    with sqlite3.connect("messages.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (recipient, message, spotify_url) VALUES (?, ?, ?)",
                       (recipient, message, spotify_url))
    return redirect(url_for('send_song'))

@app.route('/browse', methods=['GET'])
def browse():
    recipient = request.args.get("recipient")
    messages = []  # Initialize messages as an empty list
    with sqlite3.connect("messages.db") as conn:
        cursor = conn.cursor()
        if recipient:
            cursor.execute("SELECT recipient, message, spotify_url FROM messages WHERE recipient LIKE ?", ('%' + recipient + '%',))
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