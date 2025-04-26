from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
from pypdf import PdfReader
from openai import OpenAI
import io

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# --- Add CORS Middleware ---
origins = [
    "http://localhost:3000", # Allow your Next.js frontend
    "http://127.0.0.1:3000", # Also allow this variation
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # List of origins allowed
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)
# --- End CORS Middleware ---

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("Warning: OPENAI_API_KEY not found in .env file. Summarization will fail.")
    client = None
else:
    client = OpenAI(api_key=openai_api_key)

@app.get("/")
def read_root():
    return {"message": "AI Health Records API is running!"}


# Example endpoint
@app.get("/hello")
def hello_world():
    return {"message": "Hello World"}


@app.post("/summarize-pdf/")
async def summarize_pdf(file: UploadFile = File(...)):
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured.")

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    try:
        # Read PDF content
        pdf_content = await file.read()
        pdf_stream = io.BytesIO(pdf_content)
        reader = PdfReader(pdf_stream)
        
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text: # Check if text extraction was successful
                text += page_text + "\n"

        if not text:
             raise HTTPException(status_code=400, detail="Could not extract text from PDF. The PDF might be image-based or empty.")

        # Prepare the prompt based on product_spec.md
        prompt = f"""
        You are a clinical summarization assistant. Given the following medical record text extracted from a PDF, please extract key information such as demographics, chief complaint, history of present illness, past medical history, medications, allergies, physical examination findings, laboratory results, imaging results, diagnoses/assessment, and treatment plan. 

        Format the output clearly, first listing extracted entities perhaps in a structured format (like key-value pairs or a table if appropriate), and then provide a concise narrative summary suitable for a clinician's quick review.

        Extracted Text:
        {text}
        """

        # Call OpenAI API for summarization (using GPT-4 Turbo as specified)
        completion = client.chat.completions.create(
            model="gpt-4-turbo", # Specified in product_spec.md
            messages=[
                {"role": "system", "content": "You are a clinical summarization assistant."}, 
                {"role": "user", "content": prompt}
            ]
        )

        summary = completion.choices[0].message.content
        return {"filename": file.filename, "summary": summary}

    except Exception as e:
        print(f"Error processing PDF: {e}") # Log the error server-side
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000)) # Default to 8000 if PORT not set
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) # Enable reload for development
