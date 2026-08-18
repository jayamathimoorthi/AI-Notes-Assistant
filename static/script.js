const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendButton = document.getElementById("send-button");

const fileInput = document.getElementById("file-input");
const fileName = document.getElementById("file-name");


// ===============================
// PDF UPLOAD
// ===============================

fileInput.addEventListener("change", async function () {

    if (fileInput.files.length === 0) {
        fileName.textContent = "No file selected";
        return;
    }

    const file = fileInput.files[0];

    fileName.textContent = "Uploading " + file.name + "...";

    const formData = new FormData();

    formData.append("file", file);

    try {

        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (data.message) {

            fileName.textContent = "✓ " + file.name;

            addMessage(
                "Your notes are ready! You can now ask questions from the uploaded PDF.",
                "bot"
            );

        } else {

            fileName.textContent = "Upload failed";

            addMessage(
                "Error: " + (data.error || "Unable to upload PDF."),
                "bot"
            );
        }

    } catch (error) {

        console.error(error);

        fileName.textContent = "Upload failed";

        addMessage(
            "Unable to connect to the server.",
            "bot"
        );
    }

});


// ===============================
// ADD MESSAGE
// ===============================

function addMessage(message, type) {

    const messageDiv = document.createElement("div");

    messageDiv.classList.add("message");

    if (type === "user") {
        messageDiv.classList.add("user-message");
    } else {
        messageDiv.classList.add("bot-message");
    }

    const contentDiv = document.createElement("div");

    contentDiv.classList.add("message-content");

    contentDiv.innerHTML = message
    .replace(/\n\s*\n/g, "<br><br>")
    .replace(/\n/g, "<br>");

    messageDiv.appendChild(contentDiv);

    chatBox.appendChild(messageDiv);

    chatBox.scrollTop = chatBox.scrollHeight;
}


// ===============================
// ASK AI
// ===============================

async function sendMessage() {

    const message = userInput.value.trim();

    if (message === "") {
        return;
    }

    addMessage(message, "user");

    userInput.value = "";

    addMessage("Thinking...", "bot");

    try {

        const response = await fetch("/ask", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                note: message
            })

        });

        const data = await response.json();

        const messages = chatBox.querySelectorAll(".bot-message");

        if (messages.length > 0) {
            messages[messages.length - 1].remove();
        }

        if (data.answer) {

            addMessage(data.answer, "bot");

        } else if (data.error) {

            addMessage(
                "Error: " + data.error,
                "bot"
            );

        } else {

            addMessage(
                "No answer received.",
                "bot"
            );
        }

    } catch (error) {

        console.error(error);

        const messages = chatBox.querySelectorAll(".bot-message");

        if (messages.length > 0) {
            messages[messages.length - 1].remove();
        }

        addMessage(
            "Unable to connect to the AI server.",
            "bot"
        );
    }
}


// ===============================
// SEND BUTTON
// ===============================

sendButton.addEventListener(
    "click",
    sendMessage
);


// ===============================
// ENTER KEY
// ===============================

userInput.addEventListener(
    "keydown",
    function (event) {

        if (event.key === "Enter") {
            sendMessage();
        }

    }
);