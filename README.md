# MediPlus Pharmacy - AI Ticket Management System

An AI-powered customer support ticket response generation and human review system built with Flask, SQLite, and OpenAI API.

---

## Features
- **CSV Batch Upload:** Bulk upload tickets from CSV files.
- **Few-Shot AI Draft Generation:** Generates contextual replies using OpenAI GPT-3.5-Turbo and past ticket examples.
- **Tone & Policy Enforcement:** System prompts enforce polite tone and pharmacy compliance (no medical diagnoses/prescriptions).
- **Token Truncation:** Uses `tiktoken` to dynamically fit dynamic examples within the model's token limit.
- **Human-in-the-Loop Review Interface:** Allows staff to edit drafts, leave internal review comments, and approve responses.
- **Evaluation Metrics:** Tracks character length and token count for every generated and edited draft.

---

## Local Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/muhammadadeel-se/ticket-app.git](https://github.com/muhammadadeel-se/ticket-app.git)
   cd ticket-app