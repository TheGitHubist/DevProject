import os
import unittest
import tempfile
import shutil
import sqlite3
from app import app, get_db, init_db

class AddFunctionalityTests(unittest.TestCase):
    def setUp(self):
        # Create a test database
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['DATABASE'] = self.db_path
        app.config['TESTING'] = True
        self.app = app.test_client()
        
        # Initialize test database
        with app.app_context():
            init_db()
            # Clear all tables before each test
            db = get_db()
            db.execute('DELETE FROM users')
            db.execute('DELETE FROM profiles')
            db.commit()
            
        # Create test upload folders
        self.test_upload_folder = tempfile.mkdtemp()
        app.config['UPLOAD_FOLDER'] = self.test_upload_folder
        app.config['PROFILE_PICTURES_FOLDER'] = os.path.join(self.test_upload_folder, 'profile_pics')
        os.makedirs(app.config['PROFILE_PICTURES_FOLDER'], exist_ok=True)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)
        shutil.rmtree(self.test_upload_folder)

    def test_user_registration(self):
        # Test successful registration
        response = self.app.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass',
            'confirm_password': 'testpass'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify user exists in database
        with app.app_context():
            db = get_db()
            user = db.execute('SELECT * FROM users WHERE username = ?', ['testuser']).fetchone()
            self.assertIsNotNone(user)
            self.assertEqual(user['email'], 'test@example.com')
            
            # Verify profile was created with matching username
            profile = db.execute('SELECT * FROM profiles WHERE user_id = ?', [user['id']]).fetchone()
            self.assertIsNotNone(profile)
            self.assertEqual(profile['name'], 'testuser')
            
            # Verify session was set
            with self.app.session_transaction() as sess:
                self.assertEqual(sess['user'], 'testuser')

    def test_profile_updates(self):
        # Register and login test user
        self.app.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass',
            'confirm_password': 'testpass'
        })
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        })
        
        # Test name update
        response = self.app.post('/update_name', json={'name': 'New Name'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'success', response.data)
        
        # Verify name change in database
        with app.app_context():
            db = get_db()
            profile = db.execute('SELECT name FROM profiles WHERE user_id = (SELECT id FROM users WHERE username = ?)', ['testuser']).fetchone()
            self.assertEqual(profile['name'], 'New Name')

if __name__ == '__main__':
    unittest.main()
