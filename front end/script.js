document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("translate-form");
    const fileInput = document.getElementById("file-input");
    const uploadArea = document.getElementById("upload-area");
    const fileNameDisplay = document.getElementById("file-name");
    const translateBtn = document.getElementById("translate-btn");
    
    const statusArea = document.getElementById("status-area");
    const spinner = document.getElementById("spinner");
    const statusMessage = document.getElementById("status-message");
    const downloadLink = document.getElementById("download-link");

    let selectedFile = null;

    // --- Event Listeners ---

    // Trigger file input when the upload area is clicked
    uploadArea.addEventListener("click", () => fileInput.click());

    // Handle file selection
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            handleFile(fileInput.files[0]);
        }
    });

    // Drag and drop events
    uploadArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadArea.classList.add("dragover");
    });

    uploadArea.addEventListener("dragleave", () => {
        uploadArea.classList.remove("dragover");
    });

    uploadArea.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadArea.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            // Ensure only .docx files are accepted
            if (e.dataTransfer.files[0].name.endsWith('.docx')) {
                fileInput.files = e.dataTransfer.files;
                handleFile(e.dataTransfer.files[0]);
            } else {
                showStatus("Please drop a .docx file.", "error");
            }
        }
    });

    // Form submission
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!selectedFile) {
            showStatus("Please select a file first.", "error");
            return;
        }

        await translateFile();
    });

    // --- Functions ---

    function handleFile(file) {
        selectedFile = file;
        fileNameDisplay.textContent = file.name;
        resetStatus();
    }
    
    function showStatus(message, type = "info") {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
    }

    function resetStatus() {
        spinner.hidden = true;
        downloadLink.hidden = true;
        translateBtn.disabled = false;
        statusMessage.textContent = "";
    }

    async function translateFile() {
        const direction = document.getElementById("direction").value;
        const formData = new FormData();
        formData.append("file", selectedFile);
        formData.append("direction", direction);

        // Update UI for processing
        translateBtn.disabled = true;
        spinner.hidden = false;
        downloadLink.hidden = true;
        showStatus("Translating... Please wait.", "info");

        try {
            const response = await fetch("http://127.0.0.1:8000/translate-document/", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "An unknown error occurred.");
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);

            // Update UI for success
            showStatus("Translation successful! Your download will start shortly.", "success");

            // Create a temporary anchor element
            const tempLink = document.createElement('a');
            tempLink.href = url;
            tempLink.setAttribute('download', `translated_${selectedFile.name}`);

            // Append to the DOM, click it, and then remove it
            document.body.appendChild(tempLink);
            tempLink.click();
            document.body.removeChild(tempLink);

            // Clean up the blob URL to free up memory
            window.URL.revokeObjectURL(url);

        } catch (error) {
            showStatus(`Error: ${error.message}`, "error");
        } finally {
            spinner.hidden = true;
            translateBtn.disabled = false;
        }
    }
});