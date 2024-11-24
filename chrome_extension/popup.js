document.addEventListener('DOMContentLoaded', function() {
    const dropzone = document.getElementById('dropzone');
    const summaryDiv = document.getElementById('summary');
    const loadingDiv = document.getElementById('loading');
    const API_ENDPOINT = 'http://localhost:8000/summarize';

    const style = document.createElement('style');
    style.textContent = `
        .summary {
            white-space: pre-wrap;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.5;
            padding: 20px;
        }
        .summary h1 {
            font-size: 1.5em;
            margin-bottom: 1em;
        }
        .error-message {
            color: #dc3545;
            padding: 10px;
            border-radius: 4px;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            margin-top: 10px;
        }
    `;
    document.head.appendChild(style);

    // Handle file selection via click
    dropzone.addEventListener('click', () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.accept = '.eml,.msg,.txt';
        input.onchange = (e) => handleFiles(e.target.files);
        input.click();
    });

    // Handle drag and drop
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    async function handleFiles(files) {
        if (!files || files.length === 0) {
            displayError('No files selected');
            return;
        }

        if (files.length > 10) {
            displayError('Maximum 10 files allowed');
            return;
        }

        loadingDiv.style.display = 'block';
        summaryDiv.textContent = '';
        
        try {
            const emails = await Promise.all(
                Array.from(files).map(readEmailFile)
            );

            // Filter out invalid emails
            const validEmails = emails.filter(email => 
                email && email.subject && email.sender && email.body
            );

            if (validEmails.length === 0) {
                throw new Error('No valid emails found in the selected files');
            }

            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ emails: validEmails })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (!data.summary) {
                throw new Error('No summary received from server');
            }
            
            displaySummary(data.summary);
        } catch (error) {
            console.error('Error:', error);
            displayError('Error processing emails: ' + error.message);
        } finally {
            loadingDiv.style.display = 'none';
        }
    }

    function displaySummary(summary) {
        summaryDiv.className = 'summary';
        summaryDiv.textContent = summary;
    }

    function displayError(message) {
        summaryDiv.className = 'error-message';
        summaryDiv.textContent = message;
    }

    async function readEmailFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                try {
                    const content = e.target.result;
                    const emailObj = parseEmail(content);
                    resolve(emailObj);
                } catch (error) {
                    console.error(`Error parsing file ${file.name}:`, error);
                    resolve(null); // Return null for invalid emails
                }
            };
            
            reader.onerror = () => {
                console.error(`Error reading file ${file.name}`);
                resolve(null); // Return null for unreadable files
            };

            reader.readAsText(file);
        });
    }

    function parseEmail(content) {
        if (!content || typeof content !== 'string') {
            throw new Error('Invalid email content');
        }

        const lines = content.split('\n');
        let subject = '';
        let sender = '';
        let body = '';
        let inBody = false;
        let headerFound = false;

        for (const line of lines) {
            if (line.startsWith('Subject: ')) {
                subject = line.slice(9).trim();
                headerFound = true;
            } else if (line.startsWith('From: ')) {
                sender = line.slice(6).trim();
                headerFound = true;
            } else if (inBody) {
                body += line + '\n';
            } else if (line.trim() === '') {
                inBody = true;
            }
        }

        if (!headerFound) {
            throw new Error('No email headers found');
        }

        if (!subject || !sender || !body.trim()) {
            throw new Error('Missing required email fields');
        }

        return {
            subject,
            sender,
            body: body.trim(),
            date: new Date().toISOString()
        };
    }
});