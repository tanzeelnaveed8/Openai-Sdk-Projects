from dotenv import load_dotenv
import os 
from agents import RunConfig , OpenAIChatCompletionsModel , AsyncOpenAI, set_tracing_disabled 

load_dotenv()
set_tracing_disabled(True)


api_key = os.getenv("API_KEY")
# Check if the API key is present; if not, raise an error
if not api_key:
    raise ValueError("API_KEY is not set. Please ensure it is defined in your .env file.")

#Reference: https://ai.google.dev/gemini-api/docs/openai
external_client = AsyncOpenAI(
    api_key= api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled=True
)



