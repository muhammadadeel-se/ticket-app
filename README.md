# MediPlus Pharmacy - Support Ticket Management System

A production-ready Flask web application built for MediPlus Pharmacy support teams. It integrates OpenAI models with strict prompt engineering, few-shot historical examples, dynamic token management using `tiktoken`, and real-time evaluation metrics tracking.

---

## 🚀 Live Demo & Repository Links
* **Live Application:** `https://112233.pythonanywhere.com`
* **GitHub Repository:** `https://github.com/muhammadadeel-se/ticket-app`

---

## ✨ Key Features & Implementation Highlights
1. **AI Draft Generation & Policy Compliance:** Generates empathetic support replies adhering strictly to pharmacy guidelines (prohibiting medical diagnoses or direct prescription fulfillment).
2. **Dynamic Evaluation Metrics (`tiktoken`):** Automatically calculates character lengths and token counts upon draft generation and edit, displaying metrics across dashboard tables and review pages.
3. **Database Migration & Resilience (SQLite):** Uses `PRAGMA table_info` checks in `init_db()` to safely auto-migrate missing columns (`draft_length`, `token_count`, `comment`, `status`) on legacy databases without data loss or crashes.
4. **Review & Approval Workflow:** Dedicated review interface (`/review/<id>`) allowing support leads to edit drafts, monitor evaluation metrics, leave internal comments, and approve tickets.
5. **CSV Bulk Upload:** Supports importing customer tickets via CSV files.

---

## 🛠️ Complete Setup Guide

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/muhammadadeel-se/ticket-app.git](https://github.com/muhammadadeel-se/ticket-app.git)
   cd ticket-app