// =========================================
// GET ELEMENTS
// =========================================

const pdfInput = document.getElementById("pdfInput");
const uploadArea = document.getElementById("uploadArea");
const welcomeUpload = document.getElementById("welcomeUpload");

const uploadStatus = document.getElementById("uploadStatus");
const fileStatus = document.getElementById("fileStatus");

const sendBtn = document.getElementById("sendBtn");
const questionInput = document.getElementById("questionInput");

const newChatBtn = document.getElementById("newChatBtn");
const chat = document.getElementById("chat");
const welcome = document.getElementById("welcome");

const languageSelect =
    document.getElementById("languageSelect");

const topLanguage =
    document.getElementById("topLanguage");

const menuBtn =
    document.getElementById("menuBtn");

const sidebar =
    document.querySelector(".sidebar");

const sidebarOverlay =
    document.querySelector(".sidebar-overlay");


// =========================================
// SIDEBAR
// =========================================

function openSidebar() {
    document.body.classList.add("sidebar-open");
}

function closeSidebar() {
    document.body.classList.remove("sidebar-open");
}

if (menuBtn) {
    menuBtn.addEventListener("click", function () {
        openSidebar();
    });
}

if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", function () {
        closeSidebar();
    });
}


// =========================================
// CLOSE SIDEBAR AFTER OPTION
// =========================================

function closeSidebarMobile() {

    if (window.innerWidth <= 700) {
        closeSidebar();
    }
}

if (newChatBtn) {
    newChatBtn.addEventListener(
        "click",
        closeSidebarMobile
    );
}

if (uploadArea) {
    uploadArea.addEventListener(
        "click",
        closeSidebarMobile
    );
}


// =========================================
// PDF PICKER
// =========================================

function openPdfPicker() {

    if (!pdfInput) {
        return;
    }

    pdfInput.click();
}

if (uploadArea) {

    uploadArea.addEventListener(
        "click",
        openPdfPicker
    );
}

if (welcomeUpload) {

    welcomeUpload.addEventListener(
        "click",
        openPdfPicker
    );
}


// =========================================
// PDF UPLOAD
// =========================================

if (pdfInput) {

    pdfInput.addEventListener(
        "change",
        async function () {

            const file = pdfInput.files[0];

            if (!file) {
                return;
            }

            if (
                !file.name
                    .toLowerCase()
                    .endsWith(".pdf")
            ) {

                showUploadStatus(
                    "Please select a PDF file.",
                    true
                );

                pdfInput.value = "";

                return;
            }

            await uploadPdf(file);
        }
    );
}


// =========================================
// UPLOAD FUNCTION
// =========================================

async function uploadPdf(file) {

    const formData = new FormData();

    formData.append(
        "file",
        file
    );

    showUploadStatus(
        "Uploading PDF...",
        false
    );

    if (fileStatus) {
        fileStatus.textContent =
            "Processing PDF...";
    }

    try {

        const response = await fetch(
            "/upload",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {

            throw new Error(
                data.error ||
                "PDF upload failed."
            );
        }

        // ==============================
        // SUCCESS
        // ==============================

        if (fileStatus) {

            fileStatus.textContent =
                data.filename ||
                file.name;
        }

        showUploadStatus(
            `✓ ${data.filename || file.name} uploaded successfully`,
            false
        );

        // Remove welcome screen
        if (welcome) {
            welcome.remove();
        }

        // Clear old input
        pdfInput.value = "";

        // Close mobile sidebar
        closeSidebarMobile();

        // Focus question
        if (questionInput) {
            questionInput.focus();
        }

    } catch (error) {

        console.error(
            "UPLOAD ERROR:",
            error
        );

        showUploadStatus(
            "❌ " +
            (
                error.message ||
                "PDF upload failed."
            ),
            true
        );

        if (fileStatus) {

            fileStatus.textContent =
                "PDF upload failed";
        }

        pdfInput.value = "";
    }
}


// =========================================
// UPLOAD STATUS
// =========================================

function showUploadStatus(
    message,
    isError = false
) {

    if (!uploadStatus) {
        return;
    }

    uploadStatus.textContent =
        message;

    uploadStatus.style.color =
        isError
            ? "#d32f2f"
            : "#777";
}


// =========================================
// SEND QUESTION
// =========================================

if (sendBtn) {

    sendBtn.addEventListener(
        "click",
        sendQuestion
    );
}


// =========================================
// ENTER TO SEND
// =========================================

if (questionInput) {

    questionInput.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                sendQuestion();
            }
        }
    );

    // Auto resize
    questionInput.addEventListener(
        "input",
        function () {

            this.style.height = "auto";

            this.style.height =
                Math.min(
                    this
