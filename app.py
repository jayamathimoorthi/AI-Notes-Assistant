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


# =========================================================
# GLOBAL VARIABLES
# =========================================================

notes_chunks = []

previous_question = ""


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "login.html"
    )


# =========================================================
# LOGIN PAGE
# =========================================================

@app.route("/login")
def login():

    return render_template(
        "login.html"
    )


# =========================================================
# NOTES PAGE
# =========================================================

@app.route("/notes")
def notes():

    return render_template(
        "index.html"
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return jsonify({

        "status": "running",

        "gemini_api_key":
            bool(GEMINI_API_KEY),

        "pdf_uploaded":
            bool(notes_chunks),

        "total_chunks":
            len(notes_chunks)

    })


# =========================================================
# CREATE PDF CHUNKS
# =========================================================

def create_chunks(
    text,
    chunk_size=5000
):

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

@app.route(
    "/upload",
    methods=["POST"]
)
def upload_pdf():

    global notes_chunks
    global previous_question


    previous_question = ""


    # -----------------------------------------------------
    # CHECK FILE
    # -----------------------------------------------------

    if "file" not in request.files:

        return jsonify({

            "error":
                "No PDF file selected."

        }), 400


    file = request.files["file"]


    if file.filename == "":

        return jsonify({

            "error":
                "No PDF file selected."

        }), 400


    # -----------------------------------------------------
    # CHECK PDF
    # -----------------------------------------------------

    if not file.filename.lower().endswith(".pdf"):

        return jsonify({

            "error":
                "Please upload a PDF file."

        }), 400


    try:

        # -------------------------------------------------
        # READ PDF
        # -------------------------------------------------

        reader = PdfReader(file)

        full_text = ""


        for page in reader.pages:

            text = page.extract_text()


            if text:

                full_text += (
                    text + "\n"
                )


        # -------------------------------------------------
        # CHECK TEXT
        # -------------------------------------------------

        if not full_text.strip():

            return jsonify({

                "error":
                    "Could not extract text from this PDF."

            }), 400


        # -------------------------------------------------
        # CREATE CHUNKS
        # -------------------------------------------------

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


        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return jsonify({

            "success":
                True,

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

            "success":
                False,

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


    # -----------------------------------------------------
    # SORT BY SCORE
    # -----------------------------------------------------

    scored.sort(

        key=lambda x: x[0],

        reverse=True

    )


    # -----------------------------------------------------
    # SELECT RELEVANT CHUNKS
    # -----------------------------------------------------

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

@app.route(
    "/ask",
    methods=["POST"]
)
def ask_ai():

    global previous_question


    try:

        # =================================================
        # CHECK API KEY
        # =================================================

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


        # =================================================
        # CHECK GEMINI CLIENT
        # =================================================

        if client is None:

            return jsonify({

                "error":
                    "Gemini client could not be initialized."

            }), 500


        # =================================================
        # GET REQUEST DATA
        # =================================================

        data = request.get_json(
            silent=True
        )


        if not data:

            return jsonify({

                "error":
                    "Invalid request."

            }), 400


        # =================================================
        # GET QUESTION
        # =================================================

        question = data.get(
            "note",
            ""
        ).strip()


        language = data.get(
            "language",
            "English"
        )


        # =================================================
        # QUESTION CHECK
        # =================================================

        if not question:

            return jsonify({

                "error":
                    "Please enter a question."

            }), 400


        # =================================================
        # PDF CHECK
        # =================================================

        if not notes_chunks:

            return jsonify({

                "error":
                    "Please upload a PDF first."

            }), 400


        # =================================================
        # FOLLOW-UP PHRASES
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


        # =================================================
        # CHECK FOLLOW-UP
        # =================================================

        lower_question = (
            question.lower()
        )


        is_follow_up = any(

            phrase in lower_question

            for phrase
            in follow_up_phrases

        )


        # =================================================
        # SEARCH QUESTION
        # =================================================

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


        # =================================================
        # FALLBACK
        # =================================================

        if not relevant_chunks:

            relevant_chunks = (
                notes_chunks[:5]
            )


        # =================================================
        # CREATE CONTEXT
        # =================================================

        context = "\n\n".join(
            relevant_chunks
        )


        # =================================================
        # GEMINI PROMPT
        # =================================================

        prompt = f"""

You are an AI Notes Assistant.

Your job is to answer the user's question
ONLY using the information available in
the uploaded notes.

IMPORTANT RULES:

1. Do not invent information.
2. Do not use outside knowledge.
3. If the answer is not available in the
   uploaded notes, clearly say:

   "I could not find this information
   in your uploaded notes."

4. Answer clearly and accurately.
5. Use simple language.
6. Use bullet points when useful.
7. If the user asks for an explanation,
   explain based only on the notes.
8. Answer in the requested language.

Requested Language:
{language}


UPLOADED NOTES:

{context}


USER QUESTION:

{question}

"""


        # =================================================
        # CALL GEMINI
        # =================================================

        response = client.models.generate_content(

            model="gemini-2.5-flash",

            contents=prompt

        )


        # =================================================
        # GET ANSWER
        # =================================================

        answer = response.text


        if not answer:

            answer = (
                "I could not generate an answer "
                "from the uploaded notes."
            )


        # =================================================
        # SAVE PREVIOUS QUESTION
        # =================================================

        previous_question = question


        # =================================================
        # RETURN ANSWER
        # =================================================

        return jsonify({

            "success":
                True,

            "answer":
                answer

        })


    # =====================================================
    # ERROR HANDLING
    # =====================================================

    except Exception as e:

        print(
            "AI ERROR:",
            e
        )


        return jsonify({

            "success":
                False,

            "error":
                str(e)

        }), 500


# =========================================================
# GLOBAL ERROR HANDLER
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({

        "error":
            "The requested URL was not found on the server."

    }), 404


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )


    print(
        "Starting AI Notes Assistant..."
    )

    print(
        "Port:",
        port
    )


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )

