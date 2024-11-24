import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import httpx
from cryptography.fernet import Fernet
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging for debugging and tracking application activity
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) 

# Initialize FastAPI application
app = FastAPI()

# CORS Middleware to allow requests from the Chrome extension
app.add_middleware (
    CORSMiddleware,
    allow_origins=[f"chrome-extension://{os.getenv('CHROME_EXTENSION_ID')}"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"] 
)

# Generate an encryption key for encrypting email data
try:
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
    if not ENCRYPTION_KEY:
        ENCRYPTION_KEY = Fernet.generate_key()
        logger.info("Generated new encryption key")
    fernet = Fernet(ENCRYPTION_KEY)
except Exception as e:
    logger.error(f"Error initializing encryption: {str(e)}")
    raise

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY is not set. Ensure it's defined in the environment or .env file.")

class Email(BaseModel):
    """
    Represents an email with basic attributes.
    
    Attributes:
        subject (str): The subject of the email.
        body (str): The main content of the email.
        sender (str): The sender's email address.
        date (str): The date the email was sent.
    """

    subject: str
    body: str
    sender: str
    date: str
class EmailBatch(BaseModel):
    """
    Represents a collection of email objects for batch processing.
    
    Attributes:
        emails (List[Email]): A list of email objects.
    """

    emails: List[Email]

def encrypt_data(data: str) -> str:
    """
    Encrypts a string using Fernet encryption.
    
    Args:
        data (str): The data to encrypt.

    Returns:
        str: The encrypted data as a string.
    """
    try:
        return fernet.encrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption error: {str(e)}")
        raise ValueError("Error encrypting data")

def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypts a Fernet-encrypted string back to its original form.
    
    Args:
        encrypted_data (str): The encrypted data to decrypt.

    Returns:
        str: The decrypted original data.
    """
    try:
        return fernet.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption error: {str(e)}")
        raise ValueError("Error decrypting data")

async def process_with_groq(emails: List[Email]) -> str:
    """
    Sends a batch of emails to the Groq API for summarization.

    Args:
        emails (List[Email]): A list of email objects to process.

    Returns:
        str: The summarized content provided by the Groq API.
    """

    if not emails:
        raise ValueError("No emails provided for processing")
    
    async with httpx.AsyncClient() as client:
        email_content = "\n\n".join([
            f"Email {i + 1}:\nFrom: {email.sender}\nSubject: {email.subject}\nDate: {email.date}\nBody: {email.body}"
            for i, email in enumerate(emails)
        ])

        prompt = f"""Analyze these emails and provide a structured summary in the following format:
        🔑 KEY UPDATES
        • [List key updates and announcements here]

        📋 ACTION ITEMS
        • [List tasks and action items here]

        📅 DEADLINES & EVENTS
        • [List upcoming deadlines and events here]

        ⚡ CRITICAL INFORMATION
        • [List any urgent or critical information here]

        For each section:
        - Use bullet points (•)
        - Start each point with a capital letter
        - End each point with a period
        - Skip any section if there's no relevant information
        - Be concise but informative
        - Use proper line breaks between sections
        - Indicate from which email each point has been taken from

        Emails:
        {email_content}
        """

        try:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mixtral-8x7b-32768",
                    "messages": [
                        {"role": "system", "content": "You are an efficient email summarizer. For content types other than emails, reply with 'Sorry, I can't help you with this!"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000
                }
            )

            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        
        except Exception as e:
            logger.error(f"Error processing with Groq: {str(e)}")
            raise HTTPException(status_code=500, detail="Error processing emails")
        
@app.post("/summarize")
async def summarize_emails(email_batch: EmailBatch):
    """
    Endpoint to summarize a batch of emails.

    Args:
        email_batch (EmailBatch): A batch of email objects to summarize.

    Returns:
        dict: A dictionary containing the summary of the emails.
    """

    if not email_batch.emails:
            raise HTTPException(status_code=400, detail="No emails provided")
    
    try:
        processed_emails = []
        for email in email_batch.emails:
            try:
                # Trim email body if too long
                trimmed_body = email.body[:5000]  # Limit email body size
                
                encrypted_email = Email(
                    subject=encrypt_data(email.subject),
                    body=encrypt_data(trimmed_body),
                    sender=encrypt_data(email.sender),
                    date=email.date
                )
                
                decrypted_email = Email(
                    subject=decrypt_data(encrypted_email.subject),
                    body=decrypt_data(encrypted_email.body),
                    sender=decrypt_data(encrypted_email.sender),
                    date=email.date
                )
                
                processed_emails.append(decrypted_email)
                
            except Exception as e:
                logger.error(f"Error processing email: {str(e)}")
                continue  # Skip problematic emails instead of failing completely

        if not processed_emails:
            raise HTTPException(status_code=400, detail="No valid emails to process")

        summary = await process_with_groq(processed_emails)

        return {"summary": summary}
    
    except Exception as e:
        logger.error(f"Error in summarize_emails: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing request")

# Run the FastAPI application using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)