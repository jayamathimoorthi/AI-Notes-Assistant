from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
from google import genai
from pypdf import PdfReader


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# IMPORTANT:
# This prints only True/False.
# It NEVER prints your actual API key.
print("Gemini API Key Found:", bool(GEMINI_API_KEY))


# =========================================================
# GEMINI CLIENT
# =========================================================

client = None

if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

notes_chunks = []

previous_question = ""


# =========================================================
# ASK AI
# =========================================================

@app.route("/ask", methods=["POST"])
def ask_ai():

    global previous_question

    try:

        if not GEMINI_API_KEY:
            return jsonify({
                "error": "Gemini API key is not configured."
            }), 500

        if client is None:
            return jsonify({
                "error": "Gemini client could not be initialized."
            }), 500

        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "error": "Invalid request."
            }), 400

        question = data.get("note", "").strip()
        language = data.get("language", "English")

        if not question:
            return jsonify({
                "error": "Please enter a question."
            }), 400

        if not notes_chunks:
            return jsonify({
                "error": "Please upload a PDF first."
            }), 400

        # Follow-up question handling
        follow_up_phrases = [
            "is that all",
            "is this all",
            "anything else",
            "anything more",
            "more points",
            "more information",
            "give more",
            "explain more",
            "what else",
            "continue",
            "elaborate"
        ]

        lower_question = question.lower()

        is_follow_up = any(
            phrase in lower_question
            for phrase in follow_up_phrases
        )

        search_question = question

        if is_follow_up and previous_question:
            search_question = (
                previous_question
                + " "
                + question
            )

        # Find relevant notes
        relevant_chunks = find_relevant_chunks(
            search_question
        )

        if not relevant_chunks:
            relevant_chunks = notes_chunks[:5]

        context = "\n\n".join(relevant_chunks)

        # Gemini prompt
        prompt = f"""
You are an AI Notes Assistant.

Answer ONLY from the uploaded notes.

If the answer is not available in the notes,
say that the information is not available
in the uploaded notes.

Do not invent information.

Answer in {language}.

UPLOADED NOTES:
{context}

QUESTION:
{question}
"""

        # Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        answer = response.text

        previous_question = question

        return jsonify({
            "answer": answer
        })

    except Exception as e:

        print("AI ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# RUN FLASK
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )