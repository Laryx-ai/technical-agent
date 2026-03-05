from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

hf_token = os.getenv("HF_TOKEN")
client = InferenceClient(api_key=hf_token)

def get_hf_response(user_message: str) -> str:
    """Call HuggingFace API for text generation."""
    try:
        response = client.text_generation(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            prompt=user_message,
            max_new_tokens=512,
        )
        return response
    except Exception as e:
        return f"Error: {str(e)}"