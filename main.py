import os
import shutil
import toml
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from docx import Document
from groq import Groq
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider
from typing import Literal

# --- Initialize FastAPI App ---
app = FastAPI(
    title="Document Translation Service",
    description="Translate .docx files from Arabic to English and vice-versa.",
    version="1.0.0",
)

# --- System Prompts for Translation ---
AR_TO_EN_PROMPT = (
    "You are a professional translator. Translate the following Arabic text into "
    "natural, fluent English. **Important:** Any personal names, company names, "
    "geographical names, or other entities must remain in their original form; "
    "do not translate them. Preserve the meaning and tone of the text, and ensure readability."
)

EN_TO_AR_PROMPT = (
    "You are a professional translator. Translate the following English text into "
    "natural, fluent Arabic. **Important:** Any personal names, company names, "
    "geographical names, or other entities must remain in their original English form; "
    "do not translate them. Preserve the meaning and tone of the text, and ensure readability."
)

def get_groq_response(text_to_translate: str, system_prompt: str):
    """
    Gets the translation from the Groq API.
    """
    try:
        config = toml.load("config.toml")
        api_key = config["groq"]["api_key"]
    except (FileNotFoundError, KeyError):
        raise HTTPException(status_code=500, detail="Groq API key not found or config.toml is missing.")

    model = GroqModel('llama-3.3-70b-versatile', provider=GroqProvider(api_key=api_key))

    agent = Agent(
        model,
        system_prompt=system_prompt,
    )
    try:
        # ans = agent.run_sync(f"Text to translate:\n{text_to_translate}").output
        import asyncio
        ans = agent.run_sync(f"Text to translate:\n{text_to_translate}").output

        return ans
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling Groq API: {e}")


def translate_entire_doc(input_path: str, output_path: str, direction: Literal['ar-to-en', 'en-to-ar']):
    """
    Translates all non-empty paragraphs in a Word file.
    """
    doc = Document(input_path)
    system_prompt = AR_TO_EN_PROMPT if direction == 'ar-to-en' else EN_TO_AR_PROMPT
    for para in doc.paragraphs:
        if para.text.strip():  # Only translate non-empty paragraphs
            translated_text = get_groq_response(text_to_translate=para.text, system_prompt=system_prompt)
            para.text = translated_text

    doc.save(output_path)

def cleanup_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
    return

@app.post("/translate-document/", response_class=FileResponse)
def translate_document(
    file: UploadFile = File(..., description="The .docx file to translate."),
    direction: Literal['ar-to-en', 'en-to-ar'] = Form(..., description="The translation direction ('ar-to-en' or 'en-to-ar').")
):
    """
    Upload a .docx file and translate it.
    """
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .docx file.")

    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)

    input_path = os.path.join(temp_dir, file.filename)
    output_filename = f"translated_{file.filename}"
    output_path = os.path.join(temp_dir, output_filename)
    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        translate_entire_doc(input_path, output_path, direction)

        # return FileResponse(path=output_path, filename=output_filename, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        return FileResponse(path=output_path, filename=output_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during translation: {e}")
    finally:
        if os.path.exists(input_path): cleanup_file(input_path)
        

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    cleanup_file("temp")