// =========================
// PDF ELEMENTS
// =========================

const pdfFile = document.getElementById("pdfInput");
const uploadBtn = document.getElementById("uploadBtn");
const uploadStatus = document.getElementById("uploadStatus");


// =========================
// PDF UPLOAD BUTTON
// =========================

uploadBtn.addEventListener("click", () => {

    // Open Windows file picker
    pdfFile.click();

});


// =========================
// PDF FILE SELECTED
// =========================

pdfFile.addEventListener("change", async () => {

    const file = pdfFile.files[0];

    if (!file) {
        return;
    }


    // Check PDF
    if (!file.name.toLowerCase().endsWith(".pdf")) {

        uploadStatus.textContent =
            "Please select a PDF file.";

        uploadStatus.style.color = "red";

        pdfFile.value = "";

        return;
    }


    // Prepare file
    const formData = new FormData();

    formData.append("file", file);


    uploadStatus.textContent =
        "Uploading PDF...";

    uploadStatus.style.color =
        "#7c3aed";


    try {

        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });


        // Read response as text
        const text =
            await response.text();

        console.log(
            "Server response:",
            text
        );


        let data;


        // Convert to JSON
        try {

            data = JSON.parse(text);

        } catch (error) {

            console.error(
                "JSON Parse Error:",
                error
            );

            console.error(
                "Server returned:",
                text
            );


            uploadStatus.textContent =
                "PDF upload failed. Server error.";

            uploadStatus.style.color =
                "red";

            return;
        }


        // Check server error
        if (!response.ok) {

            uploadStatus.textContent =
                data.error ||
                "PDF upload failed.";

            uploadStatus.style.color =
                "red";

            return;
        }


        // Successful upload
        if (data.success) {

            uploadStatus.textContent =
                data.message ||
                "PDF uploaded successfully!";

            uploadStatus.style.color =
                "green";


            // Update top status
            const fileStatus =
                document.getElementById(
                    "fileStatus"
                );


            if (fileStatus) {

                fileStatus.textContent =
                    file.name;

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