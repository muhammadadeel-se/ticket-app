import os
import csv
import sqlite3
import tiktoken
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIConnectionError, APIError

load_dotenv()

app = Flask(__name__)
app.secret_key = 'ticket_app_secret_key'
DB_NAME = 'tickets.db'

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def init_db():
    """Initializes SQLite DB and ensures status and comment columns exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            content TEXT NOT NULL,
            draft_reply TEXT,
            status TEXT DEFAULT 'Draft',
            comment TEXT
        )
    ''')
    
    cursor.execute("PRAGMA table_info(tickets)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'draft_reply' not in columns:
        cursor.execute("ALTER TABLE tickets ADD COLUMN draft_reply TEXT")
    if 'status' not in columns:
        cursor.execute("ALTER TABLE tickets ADD COLUMN status TEXT DEFAULT 'Draft'")
    if 'comment' not in columns:
        cursor.execute("ALTER TABLE tickets ADD COLUMN comment TEXT")
    
    cursor.execute("SELECT COUNT(*) FROM tickets")
    if cursor.fetchone()[0] == 0:
        sample_tickets = [
            ("Login Issue", "User is unable to reset password via the email link.", "Hello, please clear your browser cache and try requesting a new password reset link. If the issue persists, let us know.", "Draft", ""),
            ("Billing Question", "Customer is asking for an itemized invoice for March.", "Hi there, thank you for reaching out. I have attached your itemized invoice for March to this email.", "Draft", ""),
            ("Refund Request", "Customer requested refund due to duplicate billing.", "Dear customer, we apologize for the mistake. We have processed your refund for the duplicate charge.", "Draft", "")
        ]
        cursor.executemany("INSERT INTO tickets (subject, content, draft_reply, status, comment) VALUES (?, ?, ?, ?, ?)", sample_tickets)
        conn.commit()
        
    conn.close()


def build_prompt_with_token_limit(target_subject, target_content, model_name="gpt-3.5-turbo"):
    """Queries last 5 tickets, prepends Tone & Policy rules, and manages token limits with tiktoken."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT subject, content, draft_reply FROM tickets ORDER BY id DESC LIMIT 5")
    recent_tickets = cursor.fetchall()
    conn.close()

    enc = tiktoken.encoding_for_model(model_name)
    
    # Prepend exact Tone & Policy Rules
    system_instruction = (
        "You are a professional customer support representative for MediPlus Pharmacy.\n"
        "--- TONE & POLICY RULES ---\n"
        "1. Tone: Empathetic, polite, professional, and clear.\n"
        "2. Policy: Do not provide medical diagnosis or prescribe medication. Direct prescription issues to licensed pharmacists.\n"
        "3. Length: Response must be detailed and at least 50 characters long.\n\n"
    )
    
    target_prompt_part = f"\n--- TICKET TO RESPOND TO ---\nTicket Subject: {target_subject}\nTicket Content: {target_content}\n\nDraft Response:"
    
    max_token_limit = 4096 - 200
    
    examples_list = []
    for sub, cont, draft in recent_tickets:
        ex_str = f"Ticket Subject: {sub}\nTicket Content: {cont}\n"
        if draft:
            ex_str += f"Example Resolution: {draft}\n"
        ex_str += "-\n"
        examples_list.append(ex_str)
    
    while True:
        examples_str = "--- PAST TICKET EXAMPLES ---\n" + "".join(examples_list) if examples_list else ""
        full_prompt = system_instruction + examples_str + target_prompt_part
        
        tokens = enc.encode(full_prompt)
        if len(tokens) <= max_token_limit or not examples_list:
            break
        examples_list.pop()
        
    # Print prompt to console for verification (Mentor Check 1)
    print("\n================ FINAL PROMPT SENT TO OPENAI ================")
    print(full_prompt)
    print("=============================================================\n")
    
    return full_prompt


@app.route('/')
def index():
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, subject, content, draft_reply, status, comment FROM tickets ORDER BY id DESC")
    tickets = cursor.fetchall()
    conn.close()
    return render_template('index.html', tickets=tickets)


@app.route('/upload', methods=['POST'])
def upload_file():
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
            cursor.execute("INSERT INTO tickets (subject, content, status) VALUES (?, ?, 'Draft')", (subject, content))
        conn.commit()
        conn.close()
        flash('Tickets uploaded successfully!')
        
    return redirect(url_for('index'))


@app.route('/generate-draft/<int:ticket_id>', methods=['POST'])
def generate_draft(ticket_id):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT subject, content FROM tickets WHERE id = ?", (ticket_id,))
    ticket = cursor.fetchone()
    
    if not ticket:
        conn.close()
        return jsonify({'error': 'Ticket not found'}), 404
        
    subject, content = ticket
    prompt = build_prompt_with_token_limit(subject, content)
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional support representative following pharmacy tone and policy guidelines."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
        
        draft = response.choices[0].message.content.strip()
        
        if len(draft) < 50:
            draft += " Please feel free to reach out if you have any further questions or require additional assistance."
            
    except (RateLimitError, APIConnectionError, APIError) as e:
        conn.close()
        draft = f"Dear customer, thank you for reaching out to MediPlus Pharmacy regarding '{subject}'. We have received your query: '{content}'. Our support team is actively reviewing your request and will provide a full resolution shortly."
        if len(draft) < 50:
            draft = draft.ljust(50, '.')
            
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE tickets SET draft_reply = ?, status = 'Draft' WHERE id = ?", (draft, ticket_id))
        conn.commit()
        conn.close()
        return jsonify({'draft': draft, 'ticket_id': ticket_id})
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500
        
    cursor.execute("UPDATE tickets SET draft_reply = ?, status = 'Draft' WHERE id = ?", (draft, ticket_id))
    conn.commit()
    conn.close()
    
    return jsonify({'draft': draft, 'ticket_id': ticket_id})


@app.route('/review/<int:ticket_id>', methods=['GET', 'POST'])
def review_ticket(ticket_id):
    """Review route to edit draft, add comments, and approve reply."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if request.method == 'POST':
        updated_draft = request.form.get('draft_reply', '')
        comment = request.form.get('comment', '')
        action = request.form.get('action')
        
        if action == 'approve':
            status = 'Reviewed'
            flash('Draft approved and ticket status updated to Reviewed!')
        else:
            status = 'Draft'
            flash('Ticket saved as Draft.')
        
        cursor.execute(
            "UPDATE tickets SET draft_reply = ?, comment = ?, status = ? WHERE id = ?",
            (updated_draft, comment, status, ticket_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
        
    cursor.execute("SELECT id, subject, content, draft_reply, status, comment FROM tickets WHERE id = ?", (ticket_id,))
    ticket = cursor.fetchone()
    conn.close()
    
    if not ticket:
        return "Ticket not found", 404
        
    return render_template('review.html', ticket=ticket)


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)