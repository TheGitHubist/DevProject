from flask import Flask, render_template, request, jsonify, redirect, url_for, session, g, send_from_directory, make_response
import os
from datetime import datetime
import sqlite3
from functools import wraps
import hashlib
from werkzeug.utils import secure_filename

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game_logic.player import Player
import requests

import json

players = {}

from game_logic.boss import Boss

# Initialize a global boss instance with a single fixed keyword
boss = Boss("The Overlord", "conquest")

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
DATABASE = 'app.db'

# Allowed file extensions for uploads

app.config['UPLOAD_FOLDER'] = template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static/uploads'))
app.config['PROFILE_FOLDER'] = template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static/profiles'))
app.config['PROFILE_PICTURES_FOLDER'] = template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static/profile_pictures'))
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
# Increase max file size to 500MB
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Ensure required folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROFILE_PICTURES_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROFILE_FOLDER'], exist_ok=True)

def get_user_pictures_folder(username):
    """Create and return the path to the user's profile pictures folder"""
    user_folder = os.path.join(app.config['PROFILE_PICTURES_FOLDER'], username)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

def allowed_file(filename):
    """Check if filename has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Database connection handling
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, timeout=10)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def init_db():
    with app.app_context():
        # Import and run the database initialization from database.py
        from database import init_db as db_init
        db_init()
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_by_username(username):
    return query_db('SELECT * FROM users WHERE username = ?', [username], one=True)

def create_user(username, email, password):
    db = get_db()
    try:
        # Start transaction
        db.execute('BEGIN TRANSACTION')
        
        app.logger.debug(f"Inserting user: {username}, {email}")
        # Insert user and get the ID
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
            (username, email, hash_password(password), datetime.now().isoformat())
        )
        user_id = cursor.lastrowid
        app.logger.debug(f"Inserted user ID: {user_id}")
        # useless
        
        if not user_id:
            db.rollback()
            raise Exception("Failed to create user - no ID returned")
        
        # Insert profile with username as name
        db.execute(
            'INSERT INTO profiles (user_id, name, background_color) VALUES (?, ?, ?)',
            (user_id, username, '#1f2937')
        )
        app.logger.debug(f"Profile created for user ID: {user_id} with name: {username}")
        
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback()
        raise Exception("Username or email already exists") from e
    except Exception as e:
        db.rollback()
        app.logger.error(f"Error creating user: {str(e)}")
        raise Exception("Failed to create user") from e

def update_user_profile(username, profile_data):
    db = get_db()
    user = get_user_by_username(username)
    if user:
        db.execute(''' 
            UPDATE profiles 
            SET name = ?, description = ?, picture = ?, 
                background_color = ?, background_image = ?
            WHERE user_id = ?
        ''', (
            username,
            profile_data.get('description', ''),
            profile_data.get('picture'),
            profile_data.get('background_color', '#f3f4f6'),
            profile_data.get('background_image'),
            user['id']
        ))
        db.commit()

@app.route('/')
def root():
    session.pop('user', None)
    return redirect('/login')

@app.route('/profile_picture/<username>')
def get_profile_picture(username):
    """Serve profile picture from filesystem"""
    user = get_user_by_username(username)
    if not user:
        return '', 404
        
    profile = query_db('SELECT picture FROM profiles WHERE user_id = ?', [user['id']], one=True)
    if not profile or not profile['picture']:
        # Return default avatar if no profile picture exists
        return redirect(url_for('static', filename='default-avatar.png'))
        
    try:
        # Convert URL path to filesystem path
        picture_url = profile['picture']
        if picture_url.startswith('/static/'):
            static_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
            file_path = os.path.join(static_folder_path, picture_url[len('/static/'):])
        else:
            file_path = picture_url
        
        # Check if file exists
        if not os.path.exists(file_path):
            return redirect(url_for('static', filename='default-avatar.png'))
            
        # Send file from filesystem
        return send_from_directory(
            os.path.dirname(file_path),
            os.path.basename(file_path)
        )
    except Exception as e:
        app.logger.error(f"Error serving profile picture: {str(e)}")
        return redirect(url_for('static', filename='default-avatar.png'))

def save_user_profile(username, profile_data):
    """Wrapper function that calls update_user_profile"""
    update_user_profile(username, profile_data)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def load_user_profile(username):
    """Load user profile from database"""
    user = get_user_by_username(username)
    if not user:
        return None
        
    profile = query_db('SELECT * FROM profiles WHERE user_id = ?', [user['id']], one=True)
    if profile:
        background_image_url = None
        if 'background_image' in profile.keys() and profile['background_image']:
            # Convert filesystem path to URL path
            background_image_url = profile['background_image']
            if not background_image_url.startswith('/'):
                background_image_url = '/' + background_image_url
        return {
            'name': profile['name'],
            'picture': profile['picture'] if 'picture' in profile.keys() else None,
            'background_color': profile['background_color'] if 'background_color' in profile.keys() else '#1f2937',
            'background_image': background_image_url,
            'description': profile['description'] if 'description' in profile.keys() else ''
        }
    return {
        'name': username,
        'picture': None,
        'background_color': '#1f2937',
        'background_image': None,
        'description': ''
    }


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not username or not email or not password:
            return render_template('register.html', error='All fields are required')
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        
        # Check if username exists
        if get_user_by_username(username):
            return render_template('register.html', error='Username already exists')
        
        # Check if email exists
        existing_user = query_db('SELECT * FROM users WHERE email = ?', [email], one=True)
        if existing_user:
            return render_template('register.html', error='Email already registered')
        
        # Create new user
        try:
            create_user(username, email, password)
            # Log the user in
            session['user'] = username
            return redirect(url_for('index'))
        except Exception as e:
            return render_template('register.html', error=str(e))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.pop('user', None)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = get_user_by_username(username)
        if user and user['password_hash'] == hash_password(password):
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def index():
    if 'user' in session:
        username = session['user']
        profile_data = load_user_profile(username)
        return render_template('index.html', profile=profile_data)
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    username = session['user']
    profile_data = load_user_profile(username)
    return render_template('profile.html', profile=profile_data)

@app.route('/upload_profile_picture', methods=['GET'])
@login_required
def upload_profile_picture():
    return render_template('upload_profile_picture.html')

@app.route('/update_profile_picture', methods=['POST'])
@login_required
def update_profile_picture():
    if 'picture' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['picture']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if file and allowed_file(file.filename):
        try:
            username = session['user']
            filename = secure_filename(file.filename)
            user_pictures_folder = get_user_pictures_folder(username)
            filepath = os.path.join(user_pictures_folder, filename)
            file.save(filepath)
            
            # Update profile data
            profile_data = load_user_profile(username)
            picture_url = f'/static/profile_pictures/{username}/{filename}'
            profile_data['picture'] = picture_url
            save_user_profile(username, profile_data)
            # Update database with file path
            db = get_db()
            user = get_user_by_username(username)
            if not user:
                return jsonify({'success': False, 'error': 'User not found'})
            app.logger.debug(f"Updating profile picture for user: {username}, file path: {filepath} picture_url: {picture_url}")
            db.execute(
                'UPDATE profiles SET picture = ? WHERE user_id = ?',
                (picture_url, user['id'])
            )
            db.commit()
            return jsonify({
                'success': True,
                'picture_url': picture_url
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    
    return jsonify({'success': False, 'error': 'Invalid file type'})
            
            
            
            
    
@app.route('/update_background_image', methods=['POST'])
@login_required
def update_background_image():
    try:
        username = session['user']
        profile = load_user_profile(username)
        
        # Handle background color
        if 'color' in request.form:
            profile['background_color'] = request.form['color']
            app.logger.debug(f"Updated background color: {profile['background_color']}")
        
        # Handle background image
        if 'background_image' in request.files:
            file = request.files['background_image']
            if file and allowed_file(file.filename):
                pictures_dir = os.path.join(app.config['UPLOAD_FOLDER'], username, 'pictures')
                os.makedirs(pictures_dir, exist_ok=True)
                
                filename = secure_filename(file.filename)
                file_path = os.path.join(pictures_dir, filename)
                file.save(file_path)
                file_path = file_path.replace('\\', '/')
                # Store URL path in profile for database update
                profile['background_image'] = f'/static/uploads/{username}/pictures/{filename}'
                app.logger.debug(f"Updated background image path: {profile['background_image']}")
                
        save_user_profile(username, profile)
        return jsonify({
            'success': True,
            'background_color': profile['background_color'],
            'background_image': profile['background_image']
        })
    except Exception as e:
        app.logger.error(f"Error updating background: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/background_image/<username>')
def get_background_image(username):
    """Serve background image from filesystem path stored in database"""
    app.logger.debug(f'Background image request for user: {username}')
    
    user = get_user_by_username(username)
    if not user:
        app.logger.debug(f'User not found: {username}')
        return '', 404
        
    profile = query_db('SELECT background_image FROM profiles WHERE user_id = ?', [user['id']], one=True)
    if not profile:
        app.logger.debug('No profile found for user')
        return '', 404
        
    if not profile['background_image']:
        app.logger.debug('No background image set for user')
        return '', 404
        
    try:
        # Convert URL path to filesystem path
        background_url = profile['background_image']
        if background_url.startswith('/static/'):
            static_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
            file_path = os.path.join(static_folder_path, background_url[len('/static/'):])
        else:
            file_path = background_url
        
        if not os.path.exists(file_path):
            app.logger.debug(f'Background image file not found: {file_path}')
            return '', 404
        
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        
        return send_from_directory(directory, filename)
    except Exception as e:
        app.logger.error(f"Error serving background image: {str(e)}")
        return '', 500

@app.route('/update_name', methods=['POST'])
@login_required
def update_name():
    data = request.get_json()
    if 'name' in data:
        username = session['user']
        db = get_db()
        user = get_user_by_username(username)
        if user:
            db.execute(
                'UPDATE profiles SET name = ? WHERE user_id = ?',
                (data['name'], user['id'])
            )
            db.commit()
            return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'No name provided'}), 400

@app.route('/set_easy', methods=['POST'])
@login_required
def set_easy():
    data = request.get_json()
    if 'easy' in data:
        username = session['user']
        db = get_db()
        user = get_user_by_username(username)
        if user:
            db.execute(
                'UPDATE profiles SET difficulty = ? WHERE user_id = (SELECT id FROM users WHERE username = ?)',
                (1, username)
            )
            db.commit()
            return jsonify({'success': True})
        
@app.route('/set_medium', methods=['POST'])
@login_required
def set_medium():
    data = request.get_json()
    if 'medium' in data:
        username = session['user']
        db = get_db()
        user = get_user_by_username(username)
        if user:
            db.execute(
                'UPDATE profiles SET difficulty = ? WHERE user_id = (SELECT id FROM users WHERE username = ?)',
                (2, username)
            )
            db.commit()
            return jsonify({'success': True})

@app.route('/set_hard', methods=['POST'])
@login_required
def set_hard():
    data = request.get_json()
    if 'hard' in data:
        username = session['user']
        db = get_db()
        user = get_user_by_username(username)
        if user:
            db.execute(
                'UPDATE profiles SET difficulty = ? WHERE user_id = (SELECT id FROM users WHERE username = ?)',
                (5, username)
            )
            db.commit()
            return jsonify({'success': True})

@app.route('/set_inferno', methods=['POST'])
@login_required
def set_inferno():
    data = request.get_json()
    if 'inferno' in data:
        username = session['user']
        db = get_db()
        user = get_user_by_username(username)
        print (f"Setting inferno difficulty for user: {username}")
        if user:
            db.execute(
                'UPDATE profiles SET difficulty = ? WHERE user_id = (SELECT id FROM users WHERE username = ?)',
                (10, username)
            )
            db.commit()
            return jsonify({'success': True})

@app.route('/get_background')
def get_background():
    if 'user' in session:
        username = session['user']
        profile = load_user_profile(username)
        if profile:
            return jsonify({
                'background_color': profile.get('background_color', '#1f2937'),
                'background_image': profile.get('background_image')
            })
    # Default background if no user or profile
    return jsonify({
        'background_color': '#1f2937',
        'background_image': None
    })
    
@app.route('/game')
@login_required
def game():
    username = session['user']
    fight_script = request.args.get('fight', 'fight_2')
    fight_script = 'js/' + fight_script
    # Create a new player object at the start of the game, replacing any existing one
    players[username] = Player()
    # Reset boss health when a new game starts
    global boss
    boss.health = 1000
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT difficulty FROM profiles WHERE user_id = (SELECT id FROM users WHERE username = ?)', (username,))
    difficulty = cursor.fetchone()
    print(f"Difficulty for {username}: {difficulty[0]}")
    # Set the player's difficulty based on the profile, or default to medium if not set
    if difficulty:
        players[username].setDifficulty(difficulty[0])
    else:
        # Default to medium difficulty if not set
        players[username].setDifficulty(10)
    return render_template('game.html', fight_script=fight_script)

@app.route('/api/boss', methods=['GET'])
@login_required
def get_boss():
    global boss
    return jsonify({
        'name': boss.name,
        'health': boss.health,
        'key_word': boss.key_word  # now a string
    })
    
@app.route('/api/difficulty', methods=['GET'])
@login_required
def get_difficulty():
    difficulty = players[session['user']].difficulty
    print(difficulty)
    return jsonify({
        'difficulty': difficulty
    })

@app.route('/api/boss/damage', methods=['POST'])
@login_required
def damage_boss():
    global boss
    data = request.get_json()
    damage = data.get('damage', 0)
    boss.take_dmg(damage)
    defeated = False
    if boss.health <= 0:
        defeated = True
        # Reset boss health for next round
        boss.health = 1000
    return jsonify({
        'health': boss.health,
        'defeated': defeated
    })

@app.route('/api/player/hp', methods=['GET', 'POST'])
@login_required
def player_hp():
    username = session['user']
    if username not in players:
        players[username] = Player()
    player = players[username]

    if request.method == 'GET':
        return jsonify({'hp': player.hp})

    if request.method == 'POST':
        data = request.get_json()
        damage = data.get('damage', 0)
        player.hp -= damage
        if player.hp < 0:
            player.hp = 0
        # Delete player object if hp is 0 (player died)
        if player.hp == 0:
            del players[username]
        return jsonify({'hp': player.hp})



if __name__ == '__main__':
    app.run(debug=True)
