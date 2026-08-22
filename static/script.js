// =========================
// GET HTML ELEMENTS
// =========================

const pdfInput = document.getElementById("pdfInput");
const uploadArea = document.getElementById("uploadArea");
const welcomeUpload = document.getElementById("welcomeUpload");
const uploadStatus = document.getElementById("uploadStatus");
const fileStatus = document.getElementById("fileStatus");

const sendBtn = document.getElementById("sendBtn");
const questionInput = document.getElementById("questionInput");

const newChatBtn = document.getElementById("newChatBtn");
const chat = document.getElementById("chat");

const languageSelect =
    document.getElementById("languageSelect");

const topLanguage =
    document.getElementById("topLanguage");

const menuBtn =
    document.getElementById("menuBtn");

const sidebar =
    document.querySelector(".sidebar");


// =========================
// PDF FILE PICKER
// =========================

uploadArea.addEventListener("click", () => {

    pdfInput.click();

});


welcomeUpload.addEventListener("click", () => {

    pdfInput.click();

});


// =========================
// PDF UPLOAD
// =========================

pdfInput.addEventListener("change", async () => {

    const file = pdfInput.files[0];

    if (!file) {
        return;
    }


    if (!file.name.toLowerCase().endsWith(".pdf")) {

        uploadStatus.textContent =
            "Please select a PDF file.";

        uploadStatus.style.color = "red";

        pdfInput.value = "";

        return;
    }


    uploadStatus.textContent =
        "Uploading PDF... Please wait.";

    uploadStatus.style.color =
        "#7c3aed";


    const formData = new FormData();

    formData.append("file", file);


    try {

        const response = await fetch("/upload", {

            method: "POST",

            body: formData

        });


        const text =
            await response.text();


        console.log(
            "Server response:",
            text
        );


        let data;


        try {

            data = JSON.parse(text);

        } catch (error) {

            console.error(
                "JSON Parse Error:",
                error
            );

            uploadStatus.textContent =
                "PDF upload failed. Server error.";

            uploadStatus.style.color =
                "red";

            return;
        }


        if (!response.ok) {

            uploadStatus.textContent =
                data.error ||
                "PDF upload failed.";

            uploadStatus.style.color =
                "red";

            return;
        }


        if (data.success) {

            uploadStatus.textContent =
                "✓ " +
                (data.message ||
                "PDF uploaded successfully!");

            uploadStatus.style.color =
                "green";


            fileStatus.textContent =
                file.name;


            // Hide welcome screen
            const welcome =
                document.getElementById("welcome");

            if (welcome) {

                welcome.style.display =
                    "none";

            }


        } else {

            uploadStatus.textContent =
                data.error ||
                "PDF upload failed.";

            uploadStatus.style.color =
                "red";

        }


    } catch (error) {

        console.error(
            "Upload Error:",
            error
        );


        uploadStatus.textContent =
            "Unable to connect to server.";

        uploadStatus.style.color =
            "red";

    }

});


// =========================
// SEND QUESTION
// =========================

sendBtn.addEventListener("click", () => {

    sendQuestion();

});


questionInput.addEventListener("keydown", (event) => {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendQuestion();

    }

});


// =========================
// SEND QUESTION FUNCTION
// =========================

async function sendQuestion() {

    const question =
        questionInput.value.trim();


    if (!question) {

        return;

    }


    // User message
    addMessage(
        question,
        "user"
    );


    questionInput.value = "";


    // Loading message
    const loading =
        addMessage(
            "Thinking...",
            "bot"
        );


    try {

        const response =
            await fetch("/ask", {

                method: "POST",

                headers: {

                    "Content-Type":
                        "application/json"

                },

                body: JSON.stringify({

                    question: question

                })

            });


        const data =
            await response.json();


        if (data.success) {

            loading.textContent =
                data.answer;

        } else {

            loading.textContent =
                data.error ||
                "Something went wrong.";

        }


    } catch (error) {

        console.error(
            "Question Error:",
            error
        );


        loading.textContent =
            "Unable to connect to server.";

    }

}


// =========================
// ADD CHAT MESSAGE
// =========================

function addMessage(
    message,
    type
) {

    const messageDiv =
        document.createElement("div");


    messageDiv.className =
        "message " + type;


    messageDiv.textContent =
        message;


    chat.appendChild(
        messageDiv
    );


    chat.scrollTop =
        chat.scrollHeight;


    return messageDiv;

}


// =========================
// NEW CHAT
// =========================

newChatBtn.addEventListener(
    "click",
    () => {

        chat.innerHTML = "";

        uploadStatus.textContent = "";

        questionInput.value = "";

        fileStatus.textContent =
            "No PDF uploaded";


        const welcome =
            document.createElement("div");


        welcome.id =
            "welcome";

        welcome.className =
            "welcome";


        welcome.innerHTML = `

            <div class="welcome-icon">
                ✨
            </div>

            <h1>
                What would you like to learn?
            </h1>

            <p>
                Upload your PDF notes and ask
                questions from your notes.
            </p>

            <button
                id="welcomeUpload"
                class="welcome-upload"
            >
                📄 Upload PDF Notes
            </button>

        `;


        chat.appendChild(
            welcome
        );


        // Reconnect new upload button
        document
            .getElementById("welcomeUpload")
            .addEventListener(
                "click",
                () => {

                    pdfInput.click();

                }
            );

    }
);


// =========================
// LANGUAGE
// =========================

languageSelect.addEventListener(
    "change",
    () => {

        topLanguage.value =
            languageSelect.value;

    }
);


topLanguage.addEventListener(
    "change",
    () => {

        languageSelect.value =
            topLanguage.value;

    }
);


// =========================
// MENU BUTTON
// =========================

menuBtn.addEventListener(
    "click",
    () => {

        sidebar.classList.toggle(
            "open"
        );

    }
);