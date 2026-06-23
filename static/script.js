document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const fileStatus = document.getElementById('file-status');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    const extractBtn = document.getElementById('extract-btn');
    const btnLoader = document.getElementById('btn-loader');
    const resultsPanel = document.getElementById('results-panel');
    const jsonOutput = document.getElementById('json-output');
    const resetBtn = document.getElementById('reset-btn');
    const exportJsonBtn = document.getElementById('export-json');

    const resType = document.getElementById('res-type');
    const resExtractor = document.getElementById('res-extractor');
    const resTime = document.getElementById('res-time');

    let currentFile = null;
    let currentFileId = null;

    // --- File Selection ---

    browseBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFile(e.target.files[0]);
        }
    });

    // --- Drag and Drop ---

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    function formatBytes(bytes, decimals = 2) {
        if (!+bytes) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
    }

    function handleFile(file) {
        currentFile = file;
        fileName.textContent = file.name;
        fileSize.textContent = formatBytes(file.size);
        
        dropZone.classList.add('hidden');
        fileStatus.classList.remove('hidden');
        resultsPanel.classList.add('hidden');
    }

    // --- API Interaction ---

    extractBtn.addEventListener('click', async () => {
        if (!currentFile) return;

        // UI Loading State
        extractBtn.disabled = true;
        btnLoader.classList.remove('hidden');
        resultsPanel.classList.add('hidden');

        try {
            // 1. Upload File
            const formData = new FormData();
            formData.append('file', currentFile);

            const uploadRes = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!uploadRes.ok) throw new Error(`Upload failed: ${uploadRes.statusText}`);
            const uploadData = await uploadRes.json();
            currentFileId = uploadData.file_id;

            // 2. Extract Data
            const extractRes = await fetch('/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_id: currentFileId })
            });

            if (!extractRes.ok) throw new Error(`Extraction failed: ${extractRes.statusText}`);
            const extractData = await extractRes.json();

            // 3. Display Results
            displayResults(extractData);

        } catch (error) {
            alert('Error processing document: ' + error.message);
            console.error(error);
        } finally {
            extractBtn.disabled = false;
            btnLoader.classList.add('hidden');
        }
    });

    function displayResults(data) {
        // Update Stats
        resType.textContent = data.document_type || 'Unknown';
        resExtractor.textContent = data.metadata?.extractor_used || '-';
        resTime.textContent = (data.metadata?.extraction_time_ms || 0).toFixed(1) + ' ms';

        // Display JSON with syntax highlighting
        jsonOutput.textContent = JSON.stringify(data, null, 2);
        hljs.highlightElement(jsonOutput);

        // Show Panel
        resultsPanel.classList.remove('hidden');
    }

    // --- Actions ---

    resetBtn.addEventListener('click', () => {
        currentFile = null;
        currentFileId = null;
        fileInput.value = '';
        
        fileStatus.classList.add('hidden');
        resultsPanel.classList.add('hidden');
        dropZone.classList.remove('hidden');
    });

    exportJsonBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(jsonOutput.textContent)
            .then(() => {
                const originalText = exportJsonBtn.textContent;
                exportJsonBtn.textContent = 'Copied!';
                setTimeout(() => { exportJsonBtn.textContent = originalText; }, 2000);
            })
            .catch(err => console.error('Failed to copy', err));
    });
});
