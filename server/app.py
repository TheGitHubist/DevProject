from flask import Flask, render_template, request
from flask_sock import Sock
import asyncio
from websocket_server import WebSocketServer
import socket
import threading
from static.backup.backup_handler import BackupHandler

import os

# Get absolute path to client directory
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
client_dir = os.path.join(base_dir, 'client')

app = Flask(__name__,
            template_folder=os.path.join(client_dir, 'templates'),
            static_folder=os.path.join(client_dir, 'static'))

# Explicit static file route
from flask import send_from_directory

@app.route('/static/<path:filename>')
def static_files(filename):
    static_path = os.path.join(client_dir, 'static')
    print(f"Serving static file from: {static_path}/{filename}")  # Debug logging
    if not os.path.exists(os.path.join(static_path, filename)):
        print(f"File not found: {static_path}/{filename}")  # Debug logging
    return send_from_directory(static_path, filename)
sock = Sock(app)

def start_backup_scheduler():
    """Start the backup scheduler in a separate thread"""
    handler = BackupHandler()
    handler.run_scheduler()
ws_server = WebSocketServer()

@app.route('/')
def index():
    return render_template('index.html')

@sock.route('/ws')
def websocket_route(ws):
    try:
        # Verify origin if needed
        if request.headers.get('Origin'):
            if not any(origin in request.headers['Origin'] for origin in ['localhost', '127.0.0.1']):
                return
        
        # Accept all WebSocket connections
        ws.headers = [
            ('Upgrade', 'websocket'),
            ('Connection', 'Upgrade'),
            ('Sec-WebSocket-Accept', '...'),
            ('Access-Control-Allow-Origin', '*'),
        ]
        
        asyncio.run(ws_server.register(ws))
    except Exception as e:
        print(f"WebSocket error: {e}")

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == '__main__':
    # Start backup scheduler in background thread
    backup_thread = threading.Thread(target=start_backup_scheduler, daemon=True)
    backup_thread.start()

    local_ip = get_local_ip()
    print(f"\nServer running on:")
    print(f"Local: http://localhost:5000")
    print(f"Network: http://{local_ip}:5000")
    print(f"WebSocket: ws://{local_ip}:5000/ws\n")
    
    # Run Flask development server
    app.run(host='0.0.0.0', port=5000)

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['PROFILE_FOLDER'] = 'static/profiles'
app.config['PROFILE_PICTURES_FOLDER'] = 'static/profile_pictures'
app.config['ALLOWED_EXTENSIONS'] = {'mid', 'png', 'jpg', 'jpeg'}
# Increase max file size to 500MB
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Ensure required folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROFILE_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROFILE_PICTURES_FOLDER'], exist_ok=True)

# User data storage
USERS_FILE = 'users.json'
SHARED_SONGS_FILE = 'shared_songs.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
    """Load user profile from JSON file"""
    try:
        with open(get_user_profile_path(username), 'r') as f:
            profile = json.load(f)
            # Ensure background settings exist
            if 'background_color' not in profile:
                profile['background_color'] = '#1f2937'  # Default dark gray
            if 'background_image' not in profile:
                profile['background_image'] = None
            return profile
    except FileNotFoundError:
        return {
            'name': username,
            'picture': None,
            'created_at': datetime.now().isoformat(),
            'background_color': '#1f2937',  # Default dark gray
            'background_image': None
        }

def save_user_profile(username, profile_data):
    profile_path = get_user_profile_path(username)
    with open(profile_path, 'w') as f:
        json.dump(profile_data, f)

def midi_to_string_list(midi_file):
    try:
        mid = mido.MidiFile(midi_file)
        notes = []
        total_notes = 0
        max_notes = 30000  # Increased limit to 30,000 notes
        
        for track in mid.tracks:
            for msg in track:
                if total_notes >= max_notes:
                    notes.append(f"... (Showing first {max_notes} notes)")
                    return notes
                    
                if msg.type == 'note_on' and msg.velocity > 0:
                    notes.append(f"Note: {msg.note}, Velocity: {msg.velocity}, Time: {msg.time}")
                    total_notes += 1
                elif msg.type == 'note_off':
                    notes.append(f"Note Off: {msg.note}, Time: {msg.time}")
                    total_notes += 1
        
        return notes
    except Exception as e:
        raise Exception(f"Error processing MIDI file: {str(e)}")

def load_shared_songs():
    if os.path.exists(SHARED_SONGS_FILE):
        with open(SHARED_SONGS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_shared_songs(songs):
    with open(SHARED_SONGS_FILE, 'w') as f:
        json.dump(songs, f)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        users = load_users()
        
        # Validate input
        if not username or not email or not password:
            return render_template('register.html', error='All fields are required')
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        
        if username in users:
            return render_template('register.html', error='Username already exists')
        
        if any(user['email'] == email for user in users.values()):
            return render_template('register.html', error='Email already registered')
        
        # Create new user
        users[username] = {
            'email': email,
            'password': hash_password(password),
            'created_at': datetime.now().isoformat()
        }
        save_users(users)
        
        # Create initial profile
        save_user_profile(username, {
            'name': username,
            'description': '',
            'picture': None,
            'songs': [],
            'background_color': '#f3f4f6',
            'background_image': None
        })
        
        # Log the user in
        session['user'] = username
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users = load_users()
        
        if username in users and users[username]['password'] == hash_password(password):
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
    shared_songs = load_shared_songs()
    return render_template('index.html', shared_songs=shared_songs)

@app.route('/profile')
@login_required
def profile():
    username = session['user']
    profile_data = load_user_profile(username)
    return render_template('profile.html', profile=profile_data, songs=profile_data.get('songs', []))

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
            
            return jsonify({
                'success': True,
                'picture_url': picture_url
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': 'Invalid file type'})

@app.route('/update_name', methods=['POST'])
@login_required
def update_name():
    data = request.get_json()
    if 'name' in data:
        username = session['user']
        profile_data = load_user_profile(username)
        profile_data['name'] = data['name']
        save_user_profile(username, profile_data)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'No name provided'}), 400

@app.route('/add_song', methods=['POST'])
@login_required
def add_song():
    if 'song' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['song']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.mid'):
        try:
            username = session['user']
            filename = secure_filename(file.filename)
            user_upload_folder = get_user_upload_folder(username)
            filepath = os.path.join(user_upload_folder, filename)
            file.save(filepath)
            
            # Verify the file is a valid MIDI file
            mid = mido.MidiFile(filepath)
            
            profile_data = load_user_profile(username)
            song_data = {
                'id': str(len(profile_data.get('songs', [])) + 1),
                'name': filename,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'filepath': filepath,
                'size': os.path.getsize(filepath),
                'duration': sum(msg.time for msg in mid.tracks[0]) if mid.tracks else 0
            }
            
            if 'songs' not in profile_data:
                profile_data['songs'] = []
            profile_data['songs'].append(song_data)
            save_user_profile(username, profile_data)
            
            return jsonify({'success': True})
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'Invalid MIDI file: {str(e)}'}), 400
    
    return jsonify({'error': 'Invalid file type. Please upload a .mid file'}), 400

@app.route('/delete_song/<song_id>', methods=['DELETE'])
@login_required
def delete_song(song_id):
    username = session['user']
    profile_data = load_user_profile(username)
    songs = profile_data.get('songs', [])
    
    for song in songs:
        if song['id'] == song_id:
            # Remove the file
            if os.path.exists(song['filepath']):
                os.remove(song['filepath'])
            # Remove from profile data
            songs.remove(song)
            profile_data['songs'] = songs
            save_user_profile(username, profile_data)
            return jsonify({'success': True})
    
    return jsonify({'error': 'Song not found'}), 404

@app.route('/convert/<int:song_id>')
@login_required
def convert_song(song_id):
    username = session['user']
    profile_data = load_user_profile(username)
    songs = profile_data.get('songs', [])
    
    print(f"Converting song ID: {song_id}")  # Debug log
    print(f"Available songs: {songs}")  # Debug log
    
    for song in songs:
        if str(song['id']) == str(song_id):  # Convert both to strings for comparison
            try:
                print(f"Found song: {song}")  # Debug log
                
                # Check if conversion results already exist
                if 'conversion_results' in song:
                    print("Using cached conversion results")  # Debug log
                    return render_template('conversion_results.html', 
                                        notes=song['conversion_results']['notes'],
                                        file_info=song['conversion_results']['file_info'])
                
                mid = mido.MidiFile(song['filepath'])
                notes = []
                max_notes = 30000  # Increased note limit
                
                for track in mid.tracks:
                    for msg in track:
                        if msg.type == 'note_on' and msg.velocity > 0:
                            # Convert MIDI note number to note name
                            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                            octave = (msg.note // 12) - 1
                            note_name = note_names[msg.note % 12]
                            note_string = f"{note_name}{octave}"
                            
                            notes.append(f"Note: {note_string}, Velocity: {msg.velocity}, Time: {msg.time}")
                            if len(notes) >= max_notes:
                                notes.append(f"... (showing first {max_notes} notes)")
                                break
                
                print(f"Generated {len(notes)} notes")  # Debug log
                
                # Store conversion results in the song data
                conversion_results = {
                    'notes': notes,
                    'file_info': {
                        'name': song['name'],
                        'size': os.path.getsize(song['filepath']),
                        'duration': sum(msg.time for msg in mid.tracks[0])
                    }
                }
                song['conversion_results'] = conversion_results
                save_user_profile(username, profile_data)
                
                # Return the conversion results
                return render_template('conversion_results.html', 
                                    notes=notes, 
                                    file_info=conversion_results['file_info'])
            except Exception as e:
                print(f"Error processing song: {str(e)}")  # Debug log
                return render_template('conversion_results.html', error=str(e))
    
    print(f"Song not found with ID: {song_id}")  # Debug log
    return render_template('conversion_results.html', error='Song not found')

@app.route('/update_background', methods=['POST'])
@login_required
def update_background():
    try:
        username = session['user']
        profile = load_user_profile(username)
        
        # Handle background color
        if 'color' in request.form:
            profile['background_color'] = request.form['color']
            app.logger.debug(f"Updated background color: {profile['background_color']}")
        
        # Handle background image
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                pictures_dir = os.path.join(app.config['UPLOAD_FOLDER'], username, 'pictures')
                os.makedirs(pictures_dir, exist_ok=True)
                
                filename = secure_filename(file.filename)
                file_path = os.path.join(pictures_dir, filename)
                file.save(file_path)
                
                profile['background_image'] = f'/static/uploads/{username}/pictures/{filename}'
                app.logger.debug(f"Updated background image: {profile['background_image']}")
        
        save_user_profile(username, profile)
        return jsonify({
            'success': True,
            'background_color': profile['background_color'],
            'background_image': profile['background_image']
        })
    except Exception as e:
        app.logger.error(f"Error updating background: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_background', methods=['GET'])
@login_required
def get_background():
    """Get user's background settings"""
    try:
        username = session['user']
        profile = load_user_profile(username)
        return jsonify({
            'background_color': profile.get('background_color', '#1f2937'),
            'background_image': profile.get('background_image')
        })
    except Exception as e:
        app.logger.error(f"Error getting background: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.mid'):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Verify the file is a valid MIDI file
            mid = mido.MidiFile(filepath)
            
            try:
                # Get file information before processing
                file_info = {
                    'name': filename,
                    'size': os.path.getsize(filepath),
                    'duration': sum(msg.time for msg in mid.tracks[0]) if mid.tracks else 0
                }
                
                # Process the MIDI file
                notes = midi_to_string_list(filepath)
                
                # Clean up the uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                return jsonify({
                    'notes': notes,
                    'file_info': file_info
                })
            except Exception as e:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({'error': str(e)}), 500
                
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'Invalid MIDI file: {str(e)}'}), 400
    
    return jsonify({'error': 'Invalid file type. Please upload a .mid file'}), 400

@app.route('/share_song/<int:song_id>', methods=['POST'])
@login_required
def share_song(song_id):
    username = session['user']
    profile_data = load_user_profile(username)
    songs = profile_data.get('songs', [])
    
    for song in songs:
        if str(song['id']) == str(song_id):
            shared_songs = load_shared_songs()
            
            # Check if song is already shared
            if any(s['id'] == song_id for s in shared_songs):
                return jsonify({'success': False, 'error': 'Song is already shared'})
            
            # Add song to shared songs
            shared_song = {
                'id': song['id'],
                'name': song['name'],
                'filepath': song['filepath'],
                'size': song['size'],
                'date': song['date'],
                'shared_by': username,
                'conversion_results': song.get('conversion_results')
            }
            shared_songs.append(shared_song)
            save_shared_songs(shared_songs)
            
            # Update song in user's profile
            song['is_shared'] = True
            save_user_profile(username, profile_data)
            
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Song not found'})

@app.route('/unshare_song/<int:song_id>', methods=['POST'])
@login_required
def unshare_song(song_id):
    username = session['user']
    profile_data = load_user_profile(username)
    songs = profile_data.get('songs', [])
    
    for song in songs:
        if str(song['id']) == str(song_id):
            shared_songs = load_shared_songs()
            
            # Remove song from shared songs
            shared_songs = [s for s in shared_songs if s['id'] != song_id]
            save_shared_songs(shared_songs)
            
            # Update song in user's profile
            song['is_shared'] = False
            save_user_profile(username, profile_data)
            
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Song not found'})

@app.route('/download_shared_song/<int:song_id>')
@login_required
def download_shared_song(song_id):
    shared_songs = load_shared_songs()
    
    for song in shared_songs:
        if str(song['id']) == str(song_id):
            if os.path.exists(song['filepath']):
                return send_file(
                    song['filepath'],
                    as_attachment=True,
                    download_name=song['name']
                )
            return jsonify({'success': False, 'error': 'File not found'})
    
    return jsonify({'success': False, 'error': 'Song not found'})

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def sendtomqtt(datamqtt):
    # Define the MQTT broker details
    broker = "broker.emqx.io"
    port = 1883
    topic = "/gilbert/"
    message = datamqtt

    # Create a new MQTT client instance
    client = mqtt.Client()

    # Connect to the MQTT broker
    client.connect(broker, port, 60)

    # Publish a message to the specified topic
    client.publish(topic, message)

    # Disconnect from the broker
    client.disconnect()

    print(f"Message '{message}' sent to topic '{topic}'")
    
@app.route('/send_to_mqtt', methods=['POST'])
def send_to_mqtt():
    datamqtt = request.form.get('mqtt_data')
    if datamqtt:
        sendtomqtt(datamqtt)
        return redirect(url_for('index'))
    return 'No data provided', 400

if __name__ == '__main__':
    app.run(debug=True)