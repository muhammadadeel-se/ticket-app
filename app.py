import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

# Initialize OpenAI client (v1.0+ syntax)
# Automatically reads OPENAI_API_KEY from environment variables
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Dummy tickets data (Aapki requirement ke mutabiq)
tickets = [
    {
        "id": 1,
        "subject": "Order Status Inquiry",
        "query": "Customer wants to know when their order #1042 will arrive.",
        "draft": ""
    },
    {
        "id": 2,
        "subject": "Billing Question",
        "query": "Customer is asking for an itemized invoice for March.",
        "draft": ""
    },
    {
        "id": 3,
        "subject": "Product Availability",
        "query": "Customer is asking if Panadol Extra is back in stock.",
        "draft": ""
    }
]

@app.route("/")
def index():
    return render_template("index.html", tickets=tickets)

@app.route("/review/<int:ticket_id>", methods=["GET", "POST"])
def review_ticket(ticket_id):
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)
    if not ticket:
        return "Ticket not found", 404

    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "generate_draft":
            try:
                # Updated OpenAI API Call for openai>=1.0.0
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a polite and professional customer support agent for MediPlus Pharmacy. Keep replies concise."
                        },
                        {
                            "role": "user",
                            "content": f"Draft a helpful response for this customer query: '{ticket['query']}'"
                        }
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                
                # Extract response text using new SDK format
                ticket["draft"] = response.choices[0].message.content.strip()
                flash("Draft generated successfully!", "success")
                
            except Exception as e:
                ticket["draft"] = f"Error generating draft: {str(e)}"
                flash(f"Error: {str(e)}", "danger")

        elif action == "save_draft":
            edited_draft = request.form.get("draft_text")
            ticket["draft"] = edited_draft
            flash("Draft updated and saved successfully!", "info")

    # Evaluation metrics calculation
    char_count = len(ticket["draft"]) if ticket["draft"] else 0
    token_count = len(ticket["draft"].split()) if ticket["draft"] else 0

    return render_template(
        "review.html", 
        ticket=ticket, 
        char_count=char_count, 
        token_count=token_count
    )

if __name__ == "__main__":
    app.run(debug=True)