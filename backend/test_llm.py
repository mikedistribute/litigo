import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GOOGLE_API_KEY, GEMINI_MODEL


async def test_llm():
  llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0,
  )

  response = await llm.ainvoke([HumanMessage(content="Just say 'Yo Mike' and nothing else")])
  print("Réponse Gemini :", response.content)


asyncio.run(test_llm())