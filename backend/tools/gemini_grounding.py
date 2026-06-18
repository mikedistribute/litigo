from google import genai
from google.genai import types
from langchain_core.tools import tool
from config import GOOGLE_API_KEY, GEMINI_MODEL

_client = genai.Client(api_key=GOOGLE_API_KEY)


@tool
async def gemini_grounding_search(query: str) -> str:
  """Search the web using Gemini with Google Search grounding. Use this to find real companies,
  verify they are listed on European stock exchanges, and gather market context."""
  response = await _client.aio.models.generate_content(
    model=GEMINI_MODEL,
    contents=query,
    config=types.GenerateContentConfig(
      tools=[types.Tool(google_search=types.GoogleSearch())],
    ),
  )
  return response.text