from flask import Flask, render_template, request, jsonify, session
from pypdf import PdfReader
from google import genai
import os
import uuid
import json
import re

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "notes-assistant-secret-key"
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None


# =========================================
# HOME / LOGIN
# =========================================

@app.route("/")
def home():
    return render_template("login.html")


# =========================================
# NOTES PAGE
# =========================================

@app.route("/notes")
def notes():
    return render_template("index.html")


# =========================================
# TEXT CHUNKING
# =========================================

def create_chunks(text, chunk_size=5000):
    text = text or ""

    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []

    chunks = []

    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Try to end at a sentence/space
        if end < len(text):
            better_end = text.rfind(".", start, end)

            if better_end > start + 1000:
                end = better_end + 1
            else:
                better_end = text.rfind(" ", start, end)

                if better_end > start:
                    end = better_end

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end

    return chunks


# =========================================
# FIND RELEVANT CHUNKS
# =========================================

def find_relevant_chunks(chunks, question, max_chunks=5):
    if not chunks:
        return []

    question_words = set(
        re.findall(
            r"\b[a-zA-Z0-9]{3,}\b",
            question.lower()
        )
    )

    if not question_words:
        return chunks[:max_chunks]

    scored = []

    for index, chunk in enumerate(chunks):

        chunk_words = set(
            re.findall(
                r"\b[a-zA-Z0-9]{3,}\b",
                chunk.lower()
            )
        )

        score = len(question_words.intersection(chunk_words))

        scored.append(
            (score, index, chunk)
        )

    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    selected = [
        item[2]
        for item in scored[:max_chunks]
        if item[0] > 0
    ]

    # If no keyword match, use first chunks
    if not selected:
        selected = chunks[:max_chunks]

    return selected


# =========================================
# PDF UPLOAD
# =========================================

@app.route("/upload", methods=["POST"])
def upload_pdf():

    try:

        if "file" not in request.files:
            return jsonify({
                "success": False,
                "error": "No PDF file received."
            }), 400

        file = request.files["file"]

        if not file.filename:
            return jsonify({
                "success": False,
                "error": "Please select a PDF."
            }), 400

        if not file.filename.lower().endswith(".pdf"):
            return jsonify({
                "success": False,
                "error": "Only PDF files are allowed."
            }), 400

        # =================================
        # READ PDF
        # =================================

        reader = PdfReader(file)

        text_parts = []

        for page in reader.pages:

            try:
                page_text = page.extract_text()

                if page_text:
                    text_parts.append(page_text)

            except Exception as page_error:
                print(
                    "PAGE EXTRACTION ERROR:",
                    page_error
                )

        text = "\n".join(text_parts).strip()

        if not text:
            return jsonify({
                "success": False,
                "error": (
                    "No readable text was found in this PDF. "
                    "If it is a scanned PDF, OCR may be required."
                )
            }), 400

        # =================================
        # CREATE CHUNKS
        # =================================

        chunks = create_chunks(
            text,
            chunk_size=5000
        )

        if not chunks:
            return jsonify({
                "success": False,
                "error": "Could not process the PDF text."
            }), 400

        # =================================
        # SAVE PROCESSED NOTES
        # =================================

        file_id = str(uuid.uuid4())

        data_file = os.path.join(
            UPLOAD_FOLDER,
            file_id + ".json"
        )

        data = {
            "filename": file.filename,
            "pages": len(reader.pages),
            "characters": len(text),
            "chunks": chunks
        }

        with open(
            data_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False
            )

        # =================================
        # STORE ONLY ID IN SESSION
        # =================================

        session["notes_file"] = file_id + ".json"
        session["pdf_name"] = file.filename

        print(
            "PDF READY:",
            file.filename,
            "Pages:",
            len(reader.pages),
            "Chunks:",
            len(chunks)
        )

        return jsonify({
            "success": True,
            "message": "PDF uploaded successfully.",
            "filename": file.filename,
            "pages": len(reader.pages),
            "characters": len(text),
            "chunks": len(chunks)
        })

    except Exception as e:

        print(
            "PDF UPLOAD ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "error": (
                "Unable to process this PDF. "
                "Please try again."
            )
        }), 500


# =========================================
# ASK QUESTION
# =========================================

@app.route("/ask", methods=["POST"])
def ask_question():

    try:

        data = request.get_json(
            silent=True
        )

        if not data:
            return jsonify({
                "success": False,
                "error": "No question received."
            }), 400

        question = str(
            data.get("question", "")
        ).strip()

        language = str(
            data.get("language", "Tanglish")
        ).strip()

        if not question:
            return jsonify({
                "success": False,
                "error": "Please enter a question."
            }), 400

        # =================================
        # GET PDF
        # =================================

        notes_file = session.get(
            "notes_file"
        )

        if not notes_file:
            return jsonify({
                "success": False,
                "error": "Please upload a PDF first."
            }), 400

        data_file = os.path.join(
            UPLOAD_FOLDER,
            notes_file
        )

        if not os.path.exists(data_file):
            return jsonify({
                "success": False,
                "error": (
                    "Your uploaded PDF is no longer "
                    "available. Please upload it again."
                )
            }), 400

        # =================================
        # LOAD CHUNKS
        # =================================

        with open(
            data_file,
            "r",
            encoding="utf-8"
        ) as f:

            pdf_data = json.load(f)

        chunks = pdf_data.get(
            "chunks",
            []
        )

        # =================================
        # FIND ONLY RELEVANT CONTENT
        # =================================

        relevant_chunks = find_relevant_chunks(
            chunks,
            question,
            max_chunks=5
        )

        notes_context = "\n\n---\n\n".join(
            relevant_chunks
        )

        # =================================
        # GEMINI CHECK
        # =================================

        if client is None:
            return jsonify({
                "success": False,
                "error": (
                    "Gemini API key is not configured "
                    "on the server."
                )
            }), 500

        # =================================
        # LANGUAGE INSTRUCTION
        # =================================

        if language.lower() == "tamil":
            language_instruction = (
                "Answer in simple Tamil."
            )

        elif language.lower() == "english":
            language_instruction = (
                "Answer in clear, simple English."
            )

        else:
            language_instruction = (
                "Answer in natural Tanglish "
                "(Tamil written using English letters), "
                "unless the user clearly asks for English."
            )

        # =================================
        # PROMPT
        # =================================

        prompt = f"""
You are an AI Notes Assistant.

IMPORTANT RULES:

1. Answer ONLY from the provided PDF notes.
2. Do not use outside knowledge.
3. Do not invent information.
4. If the answer is not present in the provided notes,
   say exactly:

"I couldn't find that information in your uploaded notes."

5. Give a direct and useful answer.
6. Use short paragraphs or bullet points when useful.
7. {language_instruction}

RELEVANT CONTENT FROM THE UPLOADED PDF:

{notes_context}

USER QUESTION:

{question}
"""

        # =================================
        # GEMINI REQUEST
        # =================================

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        answer = getattr(
            response,
            "text",
            None
        )

        if not answer:
            return jsonify({
                "success": False,
                "error": "AI did not return an answer."
            }), 500

        return jsonify({
            "success": True,
            "answer": answer.strip()
        })

    except Exception as e:

        print(
            "ASK ERROR:",
            repr(e)
        )

        return jsonify({
            "success": False,
            "error": (
                "Unable to get an AI answer right now. "
                "Please try again."
            )
        }), 500


# =========================================
# NEW CHAT
# =========================================

@app.route("/new-chat", methods=["POST"])
def new_chat():

    session.pop(
        "notes_file",
        None
    )

    session.pop(
        "pdf_name",
        None
    )

    return jsonify({
        "success": True,
        "message": "New chat started."
    })


# =========================================
# TEST
# =========================================

@app.route("/test")
def test():

    return jsonify({
        "success": True,
        "message": "Backend is working."
    })


# =========================================
# RUN
# =========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
                )
