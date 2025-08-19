from flask import Flask, redirect, url_for, session, request, render_template, send_from_directory
from flask_session import Session
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Discord OAuth2 configuration
DISCORD_CLIENT_ID = 'DISCORD_CLIENT_ID'
DISCORD_CLIENT_SECRET = 'DISCORD_CLIENT_SECRET'
DISCORD_REDIRECT_URI = 'http://localhost:5000/callback'
DISCORD_API_BASE_URL = 'https://discord.com/api'

# ----------------------
# Pages
# ----------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    discord_oauth_url = f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope=identify"
    return redirect(discord_oauth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Erreur : aucun code fourni"

    # Échange le code contre un token
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': DISCORD_REDIRECT_URI,
        'scope': 'identify'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post(f"{DISCORD_API_BASE_URL}/oauth2/token", data=data, headers=headers)
    r.raise_for_status()
    token = r.json()['access_token']

    # Récupère les infos utilisateur
    headers = {'Authorization': f'Bearer {token}'}
    user = requests.get(f"{DISCORD_API_BASE_URL}/users/@me", headers=headers).json()

    session['user'] = user
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html', user=session['user'])

@app.route('/comment-creator', methods=['GET', 'POST'])
def comment_creator():
    if 'user' not in session:
        return redirect(url_for('index'))

    comment = None
    if request.method == 'POST':
        comment = {
            'name': request.form['name'],
            'tag': request.form['tag'],
            'profile_pic': request.form['profile_pic'],
            'likes': request.form['likes'],
            'text': request.form['text']
        }
    return render_template('comment_creator.html', comment=comment)

@app.route('/bot-editor', methods=['GET', 'POST'])
def bot_editor():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('editor.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403



if __name__ == "__main__":
    app.run(debug=True)
