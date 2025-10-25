import toml
from groq import Groq
from docx import Document
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider

system_prompt = (
            "You are a professional translator. Translate the following Arabic text into "
            "natural, fluent English. **Important:** Any personal names, company names, "
            "geographical names, or other entities must remain in English as their original names; "
            "do not translate them. Preserve meaning and tone of the text, and ensure readability."
        )

def get_groq_response(text_to_translate):
    
    # --- Load Groq API key from config.toml ---
    config = toml.load("config.toml")
    api_key = config["groq"]["api_key"]
    model = GroqModel('llama-3.3-70b-versatile',provider=GroqProvider(api_key=api_key))

    agent = Agent(
        model,  
        system_prompt=system_prompt,  
    )
    ans = agent.run_sync(f"Arabic text:\n{text_to_translate}").output
    return ans




def translate_entire_doc(input_path: str, output_path: str):
    """Translate all non-empty paragraphs in a Word file (Arabic → English)."""
    doc = Document(input_path)

    for para in doc.paragraphs:
        if para.text.strip():  # Only translate non-empty paragraphs
            translator =get_groq_response(text_to_translate=para.text)
            para.text = translator

    doc.save(output_path)
    print(f"✅ Full-document translation saved as: {output_path}")

# --- Run Example ---
translate_entire_doc("sample.docx", "sample_translated.docx")

