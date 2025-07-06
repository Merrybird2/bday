from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import re
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Get absolute path to database
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')

# --- Initialize DB ---
def init_db():
    print(f"📂 Initializing database at: {DB_PATH}")
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password TEXT NOT NULL
            )
        ''')
        
        # Create messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL COLLATE NOCASE,
                receiver TEXT NOT NULL COLLATE NOCASE,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add index for faster inbox queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_receiver 
            ON messages (receiver COLLATE NOCASE)
        ''')
        
        conn.commit()
        print("✅ Database initialized successfully")

# --- Home ---
@app.route('/')
def home():
    return redirect(url_for('login'))

# --- Register ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        if not username or not password:
            flash('Username and password are required!')
            return redirect(url_for('register'))
            
        hashed_pw = generate_password_hash(password)
        print(f"👤 Registering user: {username}")

        try:
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
                conn.commit()
            flash('Registered successfully! You can log in now.')
            print(f"✅ User {username} registered")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already taken!')
            print(f"❌ Username {username} already exists")
        except Exception as e:
            flash(f'Unexpected error: {e}')
            print(f"🔥 Registration error: {str(e)}")
        return redirect(url_for('register'))

    return render_template('register.html')

# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required!')
            return redirect(url_for('login'))
            
        print(f"🔐 Login attempt: {username}")

        try:
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ? COLLATE NOCASE', (username,))
                user = cursor.fetchone()

            if user and check_password_hash(user[2], password):
                session['username'] = user[1]  # Store exact username from DB
                print(f"✅ Login successful: {user[1]}")
                return redirect(url_for('birthday'))
            else:
                flash('Invalid username or password')
                print(f"❌ Invalid credentials for: {username}")
        except Exception as e:
            flash(f'Login error: {e}')
            print(f"🔥 Login error: {str(e)}")
        return redirect(url_for('login'))

    return render_template('login.html')

# --- Forgot Password ---
@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        username = request.form['username'].strip()
        new_password = request.form['new_password']
        
        if not username or not new_password:
            flash('Username and new password are required!')
            return redirect(url_for('forgot'))
            
        hashed_pw = generate_password_hash(new_password)
        print(f"🔑 Password reset for: {username}")

        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ? COLLATE NOCASE', (username,))
            user = cursor.fetchone()

            if user:
                cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_pw, user[0]))
                conn.commit()
                flash('Password updated! Please log in.')
                print(f"✅ Password updated for: {username}")
                return redirect(url_for('login'))
            else:
                flash('Username not found.')
                print(f"❌ User not found: {username}")

    return render_template('forgot.html')

# --- Inbox ---
@app.route('/inbox')
def inbox():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    print(f"📭 Fetching inbox for: {username}")
    
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            cursor = conn.cursor()
            
            # Print all messages for debugging
            cursor.execute('SELECT * FROM messages')
            all_messages = cursor.fetchall()
            print(f"📦 All messages in DB ({len(all_messages)}):")
            for msg in all_messages:
                print(f"  ID: {msg[0]}, From: {msg[1]}, To: {msg[2]}, Msg: {msg[3]}, Time: {msg[4]}")
            
            # Get user's inbox
            cursor.execute('''
                SELECT sender, message, timestamp 
                FROM messages
                WHERE LOWER(receiver) = LOWER(?)
                ORDER BY timestamp DESC
            ''', (username,))
            messages = cursor.fetchall()
            
        print(f"📥 Inbox for {username} has {len(messages)} messages")
        if messages:
            print("📬 Messages found:")
            for msg in messages:
                print(f"  From: {msg[0]}, Message: {msg[1]}, Time: {msg[2]}")
        else:
            print("📭 No messages found in inbox")
            
        return render_template('inbox.html', username=username, messages=messages)
        
    except Exception as e:
        print(f"🔥 Inbox error: {str(e)}")
        flash(f'Error loading inbox: {str(e)}')
        return redirect(url_for('birthday'))

# --- Birthday page with message form ---
@app.route('/birthday', methods=['GET', 'POST'])
def birthday():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    print(f"🎂 Birthday page for: {username}")

    if request.method == 'POST':
        receiver = request.form.get('receiver', '').strip()
        message = request.form.get('message', '')
        print(f"✉️ Sending message to: {receiver}, Content: {message}")

        # Validate inputs
        if not receiver:
            flash('Receiver is required!')
            print("❌ Receiver missing")
            return redirect(url_for('birthday'))
            
        if not message:
            flash('Message is required!')
            print("❌ Message content missing")
            return redirect(url_for('birthday'))
        
        # Basic HTML sanitization
        clean_message = re.sub(r'<[^>]*>', '', message)

        try:
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                cursor = conn.cursor()
                
                # Check if receiver exists (case-insensitive)
                cursor.execute('SELECT username FROM users WHERE LOWER(username) = LOWER(?)', (receiver,))
                receiver_data = cursor.fetchone()
                
                if receiver_data:
                    actual_receiver = receiver_data[0]
                    print(f"👤 Receiver found: {actual_receiver}")
                    
                    if actual_receiver.lower() == username.lower():
                        flash("You can't send messages to yourself!")
                        print("❌ Cannot send to self")
                    else:
                        # Insert message
                        cursor.execute('''
                            INSERT INTO messages (sender, receiver, message) 
                            VALUES (?, ?, ?)
                        ''', (username, actual_receiver, clean_message))
                        conn.commit()
                        
                        # Verify insertion
                        cursor.execute('''
                            SELECT COUNT(*) FROM messages 
                            WHERE sender = ? AND receiver = ? AND message = ?
                        ''', (username, actual_receiver, clean_message))
                        count = cursor.fetchone()[0]
                        
                        if count > 0:
                            flash(f'Message sent to {actual_receiver}!')
                            print(f"✅ Message sent to {actual_receiver}")
                        else:
                            flash('Failed to send message!')
                            print(f"❌ Message not saved to database")
                        
                        return redirect(url_for('birthday'))
                else:
                    flash(f"User '{receiver}' not found!")
                    print(f"❌ Receiver not found: {receiver}")
                    
        except Exception as e:
            flash(f'Error sending message: {str(e)}')
            print(f"🔥 Message send error: {str(e)}")
            
    return render_template('birthday.html', username=username)

# --- Database Inspector ---
@app.route('/db')
def db_inspector():
    """Debug route to show database contents"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Get all users
            cursor.execute('SELECT * FROM users')
            users = cursor.fetchall()
            
            # Get all messages
            cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC')
            messages = cursor.fetchall()
            
            # Get database schema
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            table_schemas = {}
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name})")
                table_schemas[table_name] = cursor.fetchall()
            
        return render_template('db_inspector.html', 
                              users=users, 
                              messages=messages,
                              tables=tables,
                              table_schemas=table_schemas,
                              db_path=DB_PATH)
    except Exception as e:
        return f"Database error: {str(e)}", 500

# --- Logout ---
@app.route('/logout')
def logout():
    username = session.get('username', 'Unknown')
    session.pop('username', None)
    flash('You have been logged out.')
    print(f"👋 {username} logged out")
    return redirect(url_for('login'))

# --- Run ---
if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Starting Flask Message System")
    print(f"🗄️ Database path: {DB_PATH}")
    print("="*50 + "\n")
    
    init_db()
    app.run(debug=True, port=5000)