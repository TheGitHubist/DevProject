import sqlite3
from datetime import datetime
import os
import json
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    
    # Create profiles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        picture TEXT,
        background_color TEXT DEFAULT '#f3f4f6',
        background_image TEXT,
        difficulty INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def migrate_existing_data():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Migrate users from users.json
    if os.path.exists('users.json'):
        with open('users.json', 'r') as f:
            users = json.load(f)
            for username, user_data in users.items():
                cursor.execute('''
                INSERT INTO users (username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
                ''', (username, user_data['email'], user_data['password'], user_data['created_at']))
                
                # Get the new user's ID
                user_id = cursor.lastrowid
                
                # Migrate profile data
                profile_path = f'static/profiles/{username}_profile.json'
                if os.path.exists(profile_path):
                    with open(profile_path, 'r') as pf:
                        profile_data = json.load(pf)
                        # Read image files as binary data if they exist
                        picture_data = None
                        if profile_data.get('picture'):
                            try:
                                with open(profile_data['picture'], 'rb') as img_file:
                                    picture_data = img_file.read()
                            except:
                                picture_data = None
                                
                        background_image_data = None
                        if profile_data.get('background_image'):
                            try:
                                with open(profile_data['background_image'], 'rb') as img_file:
                                    background_image_data = img_file.read()
                            except:
                                background_image_data = None
                                
                        cursor.execute('''
                        INSERT INTO profiles (user_id, name, description, picture, 
                                            background_color, background_image)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            user_id,
                            profile_data.get('name', username),
                            profile_data.get('description', ''),
                            picture_data,
                            profile_data.get('background_color', '#f3f4f6'),
                            background_image_data
                        ))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    migrate_existing_data()
    print("Database initialized and existing data migrated successfully")
