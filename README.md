# MediPlus Pharmacy - AI Support Ticket Management System

A production-ready Flask web application built for MediPlus Pharmacy customer support teams. It integrates OpenAI models with strict prompt engineering, few-shot historical examples, dynamic token management using `tiktoken`, and real-time evaluation metrics tracking.

---

## 🚀 Live Demo & Repository Links
* **Live Application (PythonAnywhere):** `https://112233.pythonanywhere.com`
* **GitHub Repository:** `https://github.com/muhammadadeel-se/ticket-app`

---

## ✨ Key Features & Implementation Highlights
1. **AI Draft Generation & Policy Compliance:** Generates empathetic, professional support replies while enforcing strict pharmacy guidelines (no medical diagnoses or direct prescriptions).
2. **Dynamic Evaluation Metrics (`tiktoken`):** Automatically computes exact character lengths and OpenAI token counts upon generation, displaying live metrics across dashboard tables and review panels.
3. **Database Migration & Persistence (SQLite):** Features automatic schema inspection (`PRAGMA table_info`) to safely add missing columns (`draft_length`, `token_count`, `comment`, `status`) without breaking existing records. Uses absolute pathing for seamless server compatibility.
4. **Review & Approval Workflow:** Dedicated review interface (`/review/<id>`) allowing leads to edit drafts, add internal comments, and transition ticket status from `Draft` to `Reviewed`.
5. **CSV Bulk Upload:** Supports importing batch support tickets via CSV files.

---

## 🛠️ Local Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/muhammadadeel-se/ticket-app.git](https://github.com/muhammadadeel-se/ticket-app.git)
   cd ticket-app