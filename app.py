import os
import csv
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'ticket_app_secret_key'
DB_NAME = 'tickets.db'

def init_db():
    """Initializes the SQLite database and creates the tickets table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Renders the main ticket list and upload form."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, subject, content FROM tickets")
    tickets = cursor.fetchall()
    conn.close()
    return render_template('index.html', tickets=tickets)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles CSV upload, parses rows, and populates the SQLite database."""
    if 'file' not in request.files:
        flash('No file part in the request.')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected.')
        return redirect(url_for('index'))
    
    if file and file.filename.endswith('.csv'):
        # Parse CSV stream
        stream = file.stream.read().decode("utf-8").splitlines()
        reader = csv.DictReader(stream)
        
        init_db()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        for row in reader:
            # Flexible column lookup supporting lowercase or capitalized headers
            subject = row.get('subject') or row.get('Subject') or 'Untitled'
            content = row.get('content') or row.get('Content') or ''
            cursor.execute("INSERT INTO tickets (subject, content) VALUES (?, ?)", (subject, content))
        
        conn.commit()
        conn.close()
        flash('Tickets uploaded and saved to SQLite successfully!')
    else:
        flash('Invalid file format. Please upload a valid .csv file.')
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)