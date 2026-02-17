import os
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))  # Load environment variables from .env file

api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key)

inputs = [{
    "role": "user",
    "content": "What is the capital of France?"
}]

response = client.beta.conversations.start(
    agent_id="ag_019c6b624db775e68e2416c5d7e8f3f8",
    inputs=inputs,
)

print(response.outputs[0].content)