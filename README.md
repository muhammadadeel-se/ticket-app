# MediPlus Pharmacy - AI Customer Support Ticket Management System

An AI-powered web application built with Flask and OpenAI API to help customer support agents draft, edit, and manage responses for incoming support tickets efficiently.

---

## 📋 Features

- **Ticket Dashboard**: View pending customer queries and support tickets.
- **AI Draft Generation**: Generate contextual, professional responses using OpenAI's GPT-3.5 model.
- **Interactive Review & Edit**: Review, edit, and finalize generated drafts before sending.
- **Real-Time Evaluation Metrics**: Monitor response character counts and estimated token metrics.

---

## 🛠️ Prerequisites

- Python 3.10+
- An active [OpenAI API Key](https://platform.openai.com/)
- Git installed on your system

---

## 🔑 API Key & Secrets Setup

To maintain security, actual credentials (such as your OpenAI API Key) are **never** committed to version control.

1. **Copy the Environment Template:**
   Duplicate the `.env.example` file to create your local `.env` configuration file:
   ```bash
   cp .env.example .env