from flask import Flask, render_template, request, jsonify, redirect, url_for, session, g
import os
from datetime import datetime
import sqlite3
from functools import wraps
import hashlib


app = Flask(__name__)
DATABASE = 'app.db'

# Database connection handling
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
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

@app.route('/profile_picture/<username>')
def get_profile_picture(username):
    """Serve profile picture from database as binary data"""
    user = get_user_by_username(username)
    if not user:
        return '', 404
        
    profile = query_db('SELECT picture FROM profiles WHERE user_id = ?', [user['id']], one=True)
    if not profile or not profile['picture']:
        return '', 404
        
    try:
        # Create response with binary data
        response = make_response(profile['picture'])
        response.headers.set('Content-Type', 'image/jpeg')
        response.headers.set('Content-Disposition', 'inline')
        return response
    except Exception as e:
        app.logger.error(f"Error serving profile picture: {str(e)}")
        return '', 500

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

def get_user_profile_path(username):
    return os.path.join(app.config['PROFILE_FOLDER'], f'{username}_profile.json')

def get_user_upload_folder(username):
    user_upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
    os.makedirs(user_upload_folder, exist_ok=True)
    return user_upload_folder

def get_user_pictures_folder(username):
    user_pictures_folder = os.path.join(app.config['PROFILE_PICTURES_FOLDER'], username)
    os.makedirs(user_pictures_folder, exist_ok=True)
    return user_pictures_folder

def load_user_profile(username):
    """Load user profile from database"""
    user = get_user_by_username(username)
    if not user:
        return None
        
    profile = query_db('SELECT * FROM profiles WHERE user_id = ?', [user['id']], one=True)
    if profile:
        return {
            'name': profile['name'],
            'picture': f'/profile_picture/{username}' if 'picture' in profile.keys() and profile['picture'] else None,
            'background_color': profile['background_color'] if 'background_color' in profile.keys() else '#1f2937',
            'background_image': profile['background_image'] if 'background_image' in profile.keys() else None,
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    username = session['user']
    profile_data = load_user_profile(username)
    return render_template('profile.html', profile=profile_data)

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
            # Read the file as binary data
            picture_data = file.read()
            
            # Validate image data
            if len(picture_data) > 5 * 1024 * 1024:  # 5MB max
                return jsonify({'success': False, 'error': 'Image too large (max 5MB)'})
                
            if not picture_data:
                return jsonify({'success': False, 'error': 'Invalid image data'})
            
            # Update database directly with binary data
            db = get_db()
            user = get_user_by_username(username)
            if not user:
                return jsonify({'success': False, 'error': 'User not found'})
                
            db.execute(
                'UPDATE profiles SET picture = ? WHERE user_id = ?',
                (picture_data, user['id'])
            )
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'Profile picture updated successfully'
            })
        except Exception as e:
            app.logger.error(f"Error updating profile picture: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': 'Invalid file type'})

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

if __name__ == '__main__':
    app.run(debug=True)
