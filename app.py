import os
import sqlite3
import csv
from io import TextIOWrapper
from flask import Flask, render_template, request, redirect, url_for, flash
import openai
import tiktoken
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_mediplus')

# Database Name and Path Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_NAME = os.path.join(BASE_DIR, 'tickets.db')

# OpenAI API Setup
openai.api_key = os.getenv('OPENAI_API_KEY')


def get_db_connection():
    """Establishes connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite DB and dynamically ensures required columns exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create base table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            content TEXT NOT NULL,
            draft_reply TEXT,
            status TEXT DEFAULT 'Draft',
            comment TEXT,
            draft_length INTEGER DEFAULT 0,
            token_count INTEGER DEFAULT 0
        )
    ''')

    # PRAGMA table_info check to safely handle schema updates on legacy DBs
    cursor.execute("PRAGMA table_info(tickets)")
    columns = [col['name'] for col in cursor.fetchall()]

    if 'draft_reply' not in columns:
        cursor.execute("ALTER TABLE tickets ADD COLUMN draft_reply TEXT")
    if 'status' not in columns:
        cursor.execute("ALTER TABLE tickets ADD COLUMN status TEXT DEFAULT 'Draft'")
    if 'comment' not in columns:
        cursor.execute("ALTER TABLE tickets ADD COLUMN comment TEXT")
    if 'draft_length' not in columns:
        cursor.execute("ALTER TABLE tickets ADD COLUMN draft_length INTEGER DEFAULT 0")
    if 'token_count' not in columns:
        cursor.execute("ALTER TABLE tickets ADD COLUMN token_count INTEGER DEFAULT 0")

    conn.commit()
    conn.close()


def calculate_metrics(text, model_name="gpt-3.5-turbo"):
    """Helper function to calculate character length and tiktoken token count."""
    if not text:
        return 0, 0
    
    char_length = len(text)
    try:
        encoding = tiktoken.encoding_for_model(model_name)
        token_count = len(encoding.encode(text))
    except Exception:
        # Fallback encoding if model specific fails
        encoding = tiktoken.get_encoding("cl100k_base")
        token_count = len(encoding.encode(text))
        
    return char_length, token_count


def generate_openai_draft(subject, content):
    """Generates support draft using OpenAI API with pharmacy policy constraints."""
    system_prompt = (
        "You are an empathetic customer support assistant for MediPlus Pharmacy. "
        "Provide clear, professional, and helpful responses to customer inquiries. "
        "POLICY CONSTRAINTS: Do not diagnose medical conditions, do not modify or issue prescriptions directly, "
        "and direct customers to emergency services or a qualified physician for medical emergencies."
    )
    user_prompt = f"Subject: {subject}\nCustomer Query: {content}\n\nDraft a helpful customer support response:"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        draft = response.choices[0].message['content'].strip()
        return draft
    except Exception as e:
        return f"Error generating draft: {str(e)}"


# Initialize Database upon application start
init_db()


@app.route('/')
def index():
    """Main Dashboard: Displays all support tickets with evaluation metrics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets ORDER BY id DESC')
    tickets = cursor.fetchall()
    conn.close()
    return render_template('index.html', tickets=tickets)


@app.route('/generate-draft/<int:ticket_id>', methods=['POST'])
def generate_draft(ticket_id):
    """Generates AI draft, calculates evaluation metrics, and updates SQLite DB."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT subject, content FROM tickets WHERE id = ?', (ticket_id,))
    ticket = cursor.fetchone()

    if ticket:
        draft = generate_openai_draft(ticket['subject'], ticket['content'])
        draft_length, token_count = calculate_metrics(draft)

        cursor.execute('''
            UPDATE tickets 
            SET draft_reply = ?, draft_length = ?, token_count = ?, status = 'Draft'
            WHERE id = ?
        ''', (draft, draft_length, token_count, ticket_id))
        
        conn.commit()
        flash('AI Draft generated successfully with metrics!')
    else:
        flash('Ticket not found.')

    conn.close()
    return redirect(url_for('index'))


@app.route('/review/<int:ticket_id>', methods=['GET', 'POST'])
def review_ticket(ticket_id):
    """Review & Edit Route: Renders metrics and saves modified responses."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        draft_reply = request.form.get('draft_reply', '')
        comment = request.form.get('comment', '')
        action = request.form.get('action')

        # Recalculate metrics for the edited text
        draft_length, token_count = calculate_metrics(draft_reply)
        status = 'Reviewed' if action == 'approve' else 'Draft'

        cursor.execute('''
            UPDATE tickets 
            SET draft_reply = ?, comment = ?, status = ?, draft_length = ?, token_count = ?
            WHERE id = ?
        ''', (draft_reply, comment, status, draft_length, token_count, ticket_id))

        conn.commit()
        conn.close()
        flash('Ticket review saved successfully!')
        return redirect(url_for('index'))

    # Fetch full ticket data including draft_length (col 6) and token_count (col 7)
    cursor.execute('SELECT id, subject, content, draft_reply, status, comment, draft_length, token_count FROM tickets WHERE id = ?', (ticket_id,))
    ticket = cursor.fetchone()
    conn.close()

    if not ticket:
        flash('Ticket not found.')
        return redirect(url_for('index'))

    return render_template('review.html', ticket=ticket)


@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    """Bulk ticket import via CSV file."""
    if 'csv_file' not in request.files:
        flash('No file selected.')
        return redirect(url_for('index'))

    file = request.files['csv_file']
    if file.filename == '':
        flash('No selected file.')
        return redirect(url_for('index'))

    if file and file.filename.endswith('.csv'):
        csv_file = TextIOWrapper(file.stream, encoding='utf-8')
        csv_reader = csv.DictReader(csv_file)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        count = 0
        for row in csv_reader:
            subject = row.get('subject') or row.get('Subject')
            content = row.get('content') or row.get('Content') or row.get('query')
            if subject and content:
                cursor.execute('INSERT INTO tickets (subject, content) VALUES (?, ?)', (subject, content))
                count += 1

        conn.commit()
        conn.close()
        flash(f'Successfully imported {count} tickets!')
    else:
        flash('Please upload a valid CSV file.')

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)