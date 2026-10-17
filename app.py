import os
import csv
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'ticket_app_secret_key'
DB_NAME = 'tickets.db'

# Initialize OpenAI client using environment variable
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def init_db():
    """Initializes SQLite DB, creates/migrates tickets table with draft_reply column, and seeds initial data."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            content TEXT NOT NULL,
            draft_reply TEXT
        )
    ''')
    
    # Check if draft_reply column exists (for database migration from Task 1)
    cursor.execute("PRAGMA table_info(tickets)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'draft_reply' not in columns:
        cursor.execute("ALTER TABLE tickets ADD COLUMN draft_reply TEXT")
    
    # Seed sample tickets if empty
    cursor.execute("SELECT COUNT(*) FROM tickets")
    if cursor.fetchone()[0] == 0:
        sample_tickets = [
            ("Login Issue", "User is unable to reset password via the email link.", "Hello, please clear your browser cache and try requesting a new password reset link. If the issue persists, let us know."),
            ("Billing Question", "Customer is asking for an itemized invoice for March.", "Hi there, thank you for reaching out. I have attached your itemized invoice for March to this email."),
            ("Refund Request", "Customer requested refund due to duplicate billing.", "Dear customer, we apologize for the mistake. We have processed your refund for the duplicate charge.")
        ]
        cursor.executemany("INSERT INTO tickets (subject, content, draft_reply) VALUES (?, ?, ?)", sample_tickets)
        conn.commit()
        
    conn.close()


def build_prompt_with_examples(target_subject, target_content):
    """Queries the 5 most recent tickets to create a few-shot prompt template."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT subject, content, draft_reply FROM tickets ORDER BY id DESC LIMIT 5")
    recent_tickets = cursor.fetchall()
    conn.close()

    prompt = "You are a helpful customer support agent. Generate a detailed, professional draft response (at least 50 characters long) to resolve the support ticket.\n\n"
    
    if recent_tickets:
        prompt += "--- PAST TICKET EXAMPLES ---\n"
        for sub, cont, draft in recent_tickets:
            prompt += f"Ticket Subject: {sub}\nTicket Content: {cont}\n"
            if draft:
                prompt += f"Example Resolution: {draft}\n"
            prompt += "-\n"

    prompt += "\n--- TICKET TO RESPOND TO ---\n"
    prompt += f"Ticket Subject: {target_subject}\n"
    prompt += f"Ticket Content: {target_content}\n\n"
    prompt += "Draft Response:"
    
    return prompt


@app.route('/')
def index():
    """Renders ticket list and upload form."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, subject, content, draft_reply FROM tickets ORDER BY id DESC")
    tickets = cursor.fetchall()
    conn.close()
    return render_template('index.html', tickets=tickets)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles CSV upload and stores tickets."""
    if 'file' not in request.files:
        flash('No file selected.')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename != '' and file.filename.endswith('.csv'):
        stream = file.stream.read().decode("utf-8").splitlines()
        reader = csv.DictReader(stream)
        
        init_db()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        for row in reader:
            subject = row.get('subject') or row.get('Subject') or 'Untitled'
            content = row.get('content') or row.get('Content') or ''
            cursor.execute("INSERT INTO tickets (subject, content) VALUES (?, ?)", (subject, content))
        conn.commit()
        conn.close()
        flash('Tickets uploaded successfully!')
        
    return redirect(url_for('index'))


@app.route('/generate-draft/<int:ticket_id>', methods=['POST'])
def generate_draft(ticket_id):
    """Route that builds the prompt, calls OpenAI API (with quota fallback), saves draft to DB, and returns JSON."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT subject, content FROM tickets WHERE id = ?", (ticket_id,))
    ticket = cursor.fetchone()
    
    if not ticket:
        conn.close()
        return jsonify({'error': 'Ticket not found'}), 404
        
    subject, content = ticket
    prompt = build_prompt_with_examples(subject, content)
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional support representative."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
        
        draft = response.choices[0].message.content.strip()
        
    except Exception as e:
        error_str = str(e)
        # Fallback if OpenAI account has insufficient quota / billing limits
        if "insufficient_quota" in error_str or "429" in error_str or "auth" in error_str.lower():
            draft = f"Dear customer, thank you for reaching out regarding '{subject}'. We have received your query: '{content}'. Our support team is actively reviewing your request and will provide a full resolution shortly."
        else:
            conn.close()
            return jsonify({'error': error_str}), 500
        
    # Save draft into database
    cursor.execute("UPDATE tickets SET draft_reply = ? WHERE id = ?", (draft, ticket_id))
    conn.commit()
    conn.close()
    
    return jsonify({'draft': draft, 'ticket_id': ticket_id})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)