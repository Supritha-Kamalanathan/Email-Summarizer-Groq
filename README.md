# Email Summarizer Chrome Extension

A Chrome extension that uses AI to automatically summarize email content, powered by FastAPI and Groq's LLM API.

## Features

- 🔒 End-to-end encryption for email data
- 📊 Structured summaries including key updates, action items, deadlines, and critical information
- 🎯 Support for multiple email file formats (.eml, .msg, .txt)
- 🚀 Fast processing using Groq's Mixtral-8x7b model
- 💡 User-friendly drag-and-drop interface

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Chrome Extension (HTML, CSS, JavaScript)
- **AI Model**: Groq API (Mixtral-8x7b-32768)
- **Security**: Fernet encryption

## Prerequisites

- Python 3.8+
- Chrome Browser
- Groq API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Supritha-Kamalanathan/Email-Summarizer-Groq.git
cd Email-Summarizer-Groq
```

2. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Install the Chrome extension:
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `chrome_extension` directory from this repository

4. Create a `.env` file in the root directory (a sample .env.example file is provided)

## Usage

1. Start the backend server:
```bash
python main.py
```

2. Click the extension icon in Chrome
3. Drag and drop email files into the extension window or click to select files
4. View the structured summary of your emails

## Project Structure

```
Email-Summarizer-Groq/
├── backend/
│   ├── main.py
│   └── requirements.txt
├── chrome_extension/
│   ├── manifest.json
│   ├── popup.html
│   └── popup.js
├── .env.example
├── LICENSE
└── README.md
```

## Security Features

- Email content is encrypted using Fernet symmetric encryption
- CORS protection for the API endpoint
- Rate limiting and file size restrictions

## API Endpoints

### POST /summarize
Accepts a batch of emails and returns an AI-generated summary.

Request body:
```json
{
    "emails": [
        {
            "subject": "string",
            "body": "string",
            "sender": "string",
            "date": "string"
        }
    ]
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

----------------------------------------------------------------------------------------------------

![Screenshot (620)](https://github.com/user-attachments/assets/39762d3e-95f0-4d74-ad64-80a42f7663a3)
