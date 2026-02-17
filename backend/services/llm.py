import os
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

def get_llm_response(user_message: str) -> str:
    try:
        response = client.beta.conversations.start(
            agent_id="ag_019c6b624db775e68e2416c5d7e8f3f8",
            inputs=[{"role": "user", "content": user_message}],
        )
        return response.outputs[0].content
    except Exception as e:
        return f"Error: {str(e)}"