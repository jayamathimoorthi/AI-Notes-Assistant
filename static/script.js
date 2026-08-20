const pdfInput =
    document.getElementById("pdfInput");

const uploadArea =
    document.getElementById("uploadArea");

const welcomeUpload =
    document.getElementById("welcomeUpload");

const uploadStatus =
    document.getElementById("uploadStatus");

const fileStatus =
    document.getElementById("fileStatus");

const questionInput =
    document.getElementById("questionInput");

const sendBtn =
    document.getElementById("sendBtn");

const chat =
    document.getElementById("chat");

const welcome =
    document.getElementById("welcome");

const languageSelect =
    document.getElementById("languageSelect");

const topLanguage =
    document.getElementById("topLanguage");

const newChatBtn =
    document.getElementById("newChatBtn");

const menuBtn =
    document.getElementById("menuBtn");

const sidebar =
    document.querySelector(".sidebar");

const recentChats =
    document.getElementById("recentChats");


let selectedLanguage = "Tanglish";


// ==========================================
// LANGUAGE
// ==========================================

languageSelect.addEventListener(
    "change",
    () => {

        selectedLanguage =
            languageSelect.value;

        topLanguage.value =
            selectedLanguage;

    }
);


topLanguage.addEventListener(
    "change",
    () => {

        selectedLanguage =
            topLanguage.value;

        languageSelect.value =
            selectedLanguage;

    }
);


// ==========================================
// OPEN FILE
// ==========================================

uploadArea.addEventListener(
    "click",
    () => {

        pdfInput.click();

    }
);


welcomeUpload.addEventListener(
    "click",
    () => {

        pdfInput.click();

    }
);


pdfInput.addEventListener(
    "change",
    () => {

        if (pdfInput.files.length > 0) {

            uploadPDF(
                pdfInput.files[0]
            );

        }

    }
);


// ==========================================
// UPLOAD PDF
// ==========================================

async function uploadPDF(file) {

    if (
        !file.name
        .toLowerCase()
        .endsWith(".pdf")
    ) {

        uploadStatus.textContent =
            "Please select a PDF file.";

        return;

    }


    uploadStatus.textContent =
        "Uploading PDF...";


    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );


    try {

        const response =
            await fetch(
                "/upload",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "PDF upload failed."
            );

        }


        uploadStatus.textContent =
            "✓ " +
            data.message +
            " (" +
            data.chunks +
            " chunks)";


        fileStatus.textContent =
            file.name;


        if (welcome) {

            welcome.style.display =
                "none";

        }


    }

    catch (error) {

        console.error(error);

        uploadStatus.textContent =
            "Error: " +
            error.message;

    }

}


// ==========================================
// SEND QUESTION
// ==========================================

sendBtn.addEventListener(
    "click",
    askQuestion
);


questionInput.addEventListener(
    "keydown",
    (event) => {

        if (
            event.key === "Enter"
            && !event.shiftKey
        ) {

            event.preventDefault();

            askQuestion();

        }

    }
);


// ==========================================
// ASK AI
// ==========================================

async function askQuestion() {

    const question =
        questionInput.value.trim();


    if (!question) {

        return;

    }


    addUserMessage(question);


    addRecentChat(question);


    questionInput.value = "";


    const loading =
        addAIMessage(
            "Thinking..."
        );


    try {

        const response =
            await fetch(
                "/ask",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        note: question,

                        language:
                            selectedLanguage

                    })

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Unable to get AI response."
            );

        }


        loading.remove();


        addAIMessage(
            formatAnswer(
                data.answer
            )
        );

    }

    catch (error) {

        console.error(error);

        loading.remove();

        addAIMessage(

            `<p class="error-text">
                Error: ${escapeHTML(error.message)}
            </p>`

        );

    }

}


// ==========================================
// USER MESSAGE
// ==========================================

function addUserMessage(text) {

    if (welcome) {

        welcome.style.display =
            "none";

    }


    const wrapper =
        document.createElement("div");


    wrapper.className =
        "message user-message";


    wrapper.innerHTML = `

        <div class="user-bubble">

            ${escapeHTML(text)}

        </div>

    `;


    chat.appendChild(wrapper);


    scrollToBottom();

}


// ==========================================
// AI MESSAGE
// ==========================================

function addAIMessage(text) {

    if (welcome) {

        welcome.style.display =
            "none";

    }


    const wrapper =
        document.createElement("div");


    wrapper.className =
        "message ai-message";


    wrapper.innerHTML = `

        <div class="ai-icon">
            AI
        </div>

        <div class="ai-content">
            ${text}
        </div>

    `;


    chat.appendChild(wrapper);


    scrollToBottom();


    return wrapper;

}


// ==========================================
// FORMAT AI ANSWER
// ==========================================

function formatAnswer(text) {

    let safe =
        escapeHTML(text);


    safe =
        safe.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );


    safe =
        safe.replace(
            /^### (.*)$/gm,
            "<h3>$1</h3>"
        );


    safe =
        safe.replace(
            /^\- (.*)$/gm,
            "<li>$1</li>"
        );


    safe =
        safe.replace(
            /(<li>.*<\/li>)/gs,
            "<ul>$1</ul>"
        );


    safe =
        safe.replace(
            /^\d+\.\s+(.*)$/gm,
            "<p><strong>$&</strong></p>"
        );


    safe =
        safe.replace(
            /\n\n/g,
            "</p><p>"
        );


    safe =
        safe.replace(
            /\n/g,
            "<br>"
        );


    return "<p>" + safe + "</p>";

}


// ==========================================
// RECENT CHAT
// ==========================================

function addRecentChat(question) {

    const item =
        document.createElement("div");


    item.className =
        "recent-item";


    item.textContent =
        question;


    recentChats.prepend(item);


    if (
        recentChats.children.length > 10
    ) {

        recentChats.removeChild(
            recentChats.lastChild
        );

    }

}


// ==========================================
// NEW CHAT
// ==========================================

newChatBtn.addEventListener(
    "click",
    () => {

        chat.innerHTML = "";

        chat.appendChild(
            createWelcome()
        );

        questionInput.value = "";

        uploadStatus.textContent = "";

    }
);


function createWelcome() {

    const div =
        document.createElement("div");


    div.className =
        "welcome";


    div.innerHTML = `

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
            class="welcome-upload"
            onclick="pdfInput.click()"
        >
            📄 Upload PDF Notes
        </button>

    `;


    return div;

}


// ==========================================
// MOBILE MENU
// ==========================================

menuBtn.addEventListener(
    "click",
    () => {

        sidebar.classList.toggle(
            "open"
        );

    }
);


// ==========================================
// SCROLL
// ==========================================

function scrollToBottom() {

    chat.scrollTop =
        chat.scrollHeight;

}


// ==========================================
// SECURITY / HTML ESCAPE
// ==========================================

function escapeHTML(text) {

    const div =
        document.createElement("div");

    div.textContent =
        text;

    return div.innerHTML;

}