# MediPlus Support Ticket AI Assistant

A production-ready Flask web application designed for MediPlus Pharmacy to automate initial customer support draft generation using the OpenAI API (`gpt-3.5-turbo`), calculate token and character evaluation metrics via `tiktoken`, and allow human-in-the-loop review before finalized responses are sent.

---

## 🛠️ Features
- **AI Draft Generation:** Automatically generates empathetic, policy-compliant support drafts for customer queries.
- **Evaluation Metrics:** Uses `tiktoken` to compute token counts and character length in real-time on generation and edit.
- **Human Review Dashboard:** Editable draft fields with instant character-count updates and approval workflow.
- **CSV Bulk Import:** Import multiple customer tickets directly via CSV upload.
- **Database Resilience:** Auto-migrating SQLite schema dynamically adds missing metric columns on startup (`PRAGMA table_info`).

---

## 🚀 Setup Instructions

### 1. Local Setup
```bash
git clone [https://github.com/muhammadadeel-se/ticket-app.git](https://github.com/muhammadadeel-se/ticket-app.git)
cd ticket-app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt