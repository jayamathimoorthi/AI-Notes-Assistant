uploadBtn.addEventListener("click", async () => {

    const file = pdfFile.files[0];

    if (!file) {
        uploadStatus.textContent = "Please select a PDF file.";
        uploadStatus.style.color = "red";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    uploadStatus.textContent = "Uploading PDF...";
    uploadStatus.style.color = "#7c3aed";

    try {

        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        // Read server response as text first
        const text = await response.text();

        console.log("Server response:", text);

        let data;

        try {
            data = JSON.parse(text);
        } catch (error) {

            console.error("JSON Parse Error:", error);
            console.error("Server returned:", text);

            uploadStatus.textContent =
                "PDF upload failed. Server error.";

            uploadStatus.style.color = "red";

            return;
        }

        if (!response.ok) {

            uploadStatus.textContent =
                data.error || "PDF upload failed.";

            uploadStatus.style.color = "red";

            return;
        }

        if (data.success) {

            uploadStatus.textContent =
                data.message || "PDF uploaded successfully!";

            uploadStatus.style.color = "green";

        } else {

            uploadStatus.textContent =
                data.error || "PDF upload failed.";

            uploadStatus.style.color = "red";
        }

    } catch (error) {

        console.error("Upload Error:", error);

        uploadStatus.textContent =
            "Unable to connect to server.";

        uploadStatus.style.color = "red";
    }
});g