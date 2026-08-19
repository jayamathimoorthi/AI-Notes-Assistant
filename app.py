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
# HOME PAGE
# =========================================================

@app.route("/")
def home():
    return render_template("login.html")


# =========================================================
# LOGIN PAGE
# =========================================================

@app.route("/login")
def login():
    return render_template("login.html")


# =========================================================
# NOTES PAGE
# =========================================================

@app.route("/notes")
def notes():
    return render_template("index.html")


# =========================================================
# CREATE PDF CHUNKS
# =========================================================

def create_chunks(text, chunk_size=5000):

    words = text.split()

    chunks = []

    current = []

    length = 0

    for word in words:

        current.append(word)

        length += len(word) + 1

        if length >= chunk_size:

            chunks.append(
                " ".join(current)
            )

            current = []

            length = 0

    if current:

        chunks.append(
            " ".join(current)
        )

    return chunks


# =========================================================
# PDF UPLOAD
# =========================================================

@app.route("/upload", methods=["POST"])
def upload_pdf():

    global notes_chunks
    global previous_question

    previous_question = ""

    if "file" not in request.files:

        return jsonify({
            "error": "No PDF file selected."
        }), 400

    file = request.files["file"]

    if file.filename == "":

        return jsonify({
            "error": "No PDF file selected."
        }), 400

    if not file.filename.lower().endswith(".pdf"):

        return jsonify({
            "error": "Please upload a PDF file."
        }), 400

    try:

        reader = PdfReader(file)

        full_text = ""

        for page in reader.pages:

            text = page.extract_text()

            if text:

                full_text += text + "\n"

        if not full_text.strip():

            return jsonify({
                "error": "Could not extract text from this PDF."
            }), 400

        notes_chunks = create_chunks(
            full_text
        )

        print(
            "PDF uploaded successfully."
        )

        print(
            "Total chunks:",
            len(notes_chunks)
        )

        return jsonify({

            "message":
                "PDF uploaded successfully.",

            "chunks":
                len(notes_chunks)

        })

    except Exception as e:

        print(
            "PDF ERROR:",
            e
        )

        return jsonify({

            "error":
                str(e)

        }), 500


# =========================================================
# FIND RELEVANT CHUNKS
# =========================================================

def find_relevant_chunks(
    question,
    max_chunks=5
):

    question_words = set(

        word.lower().strip(
            ".,?!:;()[]{}\"'"
        )

        for word in question.split()

        if len(word) > 2

    )

    scored = []

    for index, chunk in enumerate(
        notes_chunks
    ):

        chunk_words = set(

            word.lower().strip(
                ".,?!:;()[]{}\"'"
            )

            for word in chunk.split()

        )

        score = len(
            question_words.intersection(
                chunk_words
            )
        )

        scored.append(
            (
                score,
                index,
                chunk
            )
        )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    selected = [

        chunk

        for score, index, chunk
        in scored[:max_chunks]

        if score > 0

    ]

    return selected


# =========================================================
# ASK AI
# =========================================================

@app.route("/ask", methods=["POST"])
def ask_ai():

    global previous_question

    try:

        # -------------------------------------------------
        # CHECK GEMINI API KEY
        # -------------------------------------------------

        if not GEMINI_API_KEY:

            print(
                "ERROR: GEMINI_API_KEY was not found."
            )

            return jsonify({

                "error":
                "Gemini API key is not configured on the server. "
                "Please add GEMINI_API_KEY in Render Environment Variables "
                "and redeploy."

            }), 500


        # -------------------------------------------------
        # CHECK CLIENT
        # -------------------------------------------------

        if client is None:

            return jsonify({

                "error":
                "Gemini client could not be initialized."

            }), 500


        # -------------------------------------------------
        # GET REQUEST DATA
        # -------------------------------------------------

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({

                "error":
                "Invalid request."

            }), 400


        question = data.get(
            "note",
            ""
        ).strip()


        language = data.get(
            "language",
            "English"
        )


        # -------------------------------------------------
        # QUESTION CHECK
        # -------------------------------------------------

        if not question:

            return jsonify({

                "error":
                "Please enter a question."

            }), 400


        # -------------------------------------------------
        # PDF CHECK
        # -------------------------------------------------

        if not notes_chunks:

            return jsonify({

                "error":
                "Please upload a PDF first."

            }), 400


        # =================================================
        # FOLLOW-UP QUESTION
        # =================================================

        follow_up_phrases = [

            "is that all",
            "is this all",
            "that's all",
            "thats all",
            "anything else",
            "anything more",
            "more points",
            "more information",
            "give more",
            "explain more",
            "what else",
            "continue",
            "elaborate",
            "is there more",
            "is it enough"

        ]


        lower_question = (
            question.lower()
        )


        is_follow_up = any(

            phrase in lower_question

            for phrase
            in follow_up_phrases

        )


        search_question = question


        if (
            is_follow_up
            and previous_question
        ):

            search_question = (

                previous_question
                + " "
                + question

            )


        # =================================================
        # FIND RELEVANT NOTES
        # =================================================

        relevant_chunks = (
            find_relevant_chunks(
                search_question
            )
        )


        if not relevant_chunks:

            relevant_chunks = (
                notes_chunks[:5]