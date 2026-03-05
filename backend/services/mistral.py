import os
from mistralai import Mistral
from dotenv import load_dotenv
from mistralai.models import MessageOutputEntry

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

def get_llm_response(user_message: str) -> str:
    try:
        response = client.beta.conversations.start(
            agent_id="ag_019c6b624db775e68e2416c5d7e8f3f8",
            inputs=[{"role": "user", "content": user_message}],
        )
        
        response_text = next(
            (
                entry.content
                for entry in response.outputs
                if isinstance(entry, MessageOutputEntry) and isinstance(entry.content, str)
            ),
            "No text response available.",
        )
        return response_text
    except Exception as e:
        return f"Error: {str(e)}"