from flask import Flask, render_template, request, jsonify, session
from pypdf import PdfReader
import os
import uuid

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "notes-assistant-secret-key"
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================
# HOME / LOGIN
# =========================

@app.route("/")
def home():
    return render_template("login.html")


# =========================
# NOTES ASSISTANT PAGE
# =========================

@app.route("/notes")
def notes():
    return render_template("index.html")


# =========================
# PDF UPLOAD
# =========================

@app.route("/upload", methods=["POST"])
def upload_pdf():

    try:

        if "file" not in request.files:
            return jsonify({
                "success": False,
                "error": "No PDF file received"
            }), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({
                "success": False,
                "error": "Please select a PDF file"
            }), 400

        if not file.filename.lower().endswith(".pdf"):
            return jsonify({
                "success": False,
                "error": "Only PDF files are allowed"
            }), 400

        # =========================
        # READ PDF
        # =========================

        reader = PdfReader(file)

        text_parts = []

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text_parts.append(page_text)

        text = "\n".join(text_parts)

        # =========================
        # CHECK TEXT
        # =========================

        if not text.strip():

            return jsonify({
                "success": False,
                "error": "Could not extract text from this PDF"
            }), 400

        # =========================
        # SAVE TEXT TO SERVER
        # =========================

        file_id = str(uuid.uuid4())

        text_file = os.path.join(
            UPLOAD_FOLDER,
            file_id + ".txt"
        )

        with open(
            text_file,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(text)

        # IMPORTANT:
        # Only small filename stored in session
        session["notes_file"] = file_id + ".txt"

        print("PDF uploaded successfully")
        print("Pages:", len(reader.pages))
        print("Characters:", len(text))
        print("Saved:", text_file)

        return jsonify({

            "success": True,

            "message": "PDF uploaded successfully",

            "pages": len(reader.pages),

            "characters": len(text)

        })

    except Exception as e:

        print("PDF UPLOAD ERROR:", str(e))

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# =========================
# ASK QUESTION
# =========================

@app.route("/ask", methods=["POST"])
def ask_question():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "error": "No question received"
            }), 400

        question = data.get(
            "question",
            ""
        ).strip()

        if not question:

            return jsonify({
                "success": False,
                "error": "Please enter a question"
            }), 400

        # =========================
        # GET PDF FILE FROM SESSION
        # =========================

        notes_file = session.get(
            "notes_file"
        )

        if not notes_file:

            return jsonify({
                "success": False,
                "error": "Please upload a PDF first"
            }), 400

        text_file = os.path.join(
            UPLOAD_FOLDER,
            notes_file
        )

        if not os.path.exists(text_file):

            return jsonify({
                "success": False,
                "error": "Uploaded PDF data was not found. Please upload again."
            }), 400

        # =========================
        # READ PDF TEXT
        # =========================

        with open(
            text_file,
            "r",
            encoding="utf-8"
        ) as f:

            notes_text = f.read()

        # =========================
        # TEMPORARY RESPONSE
        # =========================

        # Gemini integration can be added here

        answer = (
            "Your question was received successfully. "
            "The PDF is uploaded and ready for AI processing."
        )

        return jsonify({

            "success": True,

            "answer": answer

        })

    except Exception as e:

        print("ASK ERROR:", str(e))

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# =========================
# TEST ROUTE
# =========================

@app.route("/test")
def test():

    return jsonify({

        "success": True,

        "message": "Backend is working"

    })


# =========================
# RUN SERVER
# =========================

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

