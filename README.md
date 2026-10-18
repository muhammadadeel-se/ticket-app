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

## 🔑 Environment Variables & API Key Setup

To run this application securely, you must configure your environment variables.

1. Create a `.env` file in the root directory of the project:
   ```bash
   touch .env