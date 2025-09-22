# llm_utils.py
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()

# Retrieve the API key from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize the LLM with the correct Gemini 1.5 Flash model name
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest",  # Corrected model name
    temperature=0.1,
    api_key=GOOGLE_API_KEY
)

# Classify user query
def classify_query_dynamic(query):
    prompt = f"""
Classify the query into one of the following: Finance, IT, Pharma, Stock, General Conversation, or Out-of-Scope.
Return a JSON with keys: "type", "scope".
"""
    response = llm.invoke([
        SystemMessage(content="You are a helpful financial query classifier."),
        HumanMessage(content=prompt + f"\nQuery: {query}")
    ])
    return response.content.strip()

# Generate a structured research plan
def generate_research_plan(query):
    prompt = (
        f"Create a **concise and actionable research plan** for the query: {query}.\n"
        "Use short bullet points. Each point should be clear and focused. "
        "Limit to 5 points maximum. Avoid vague or generic statements. "
        "Ensure the plan is tailored to financial research. "
        "Give in 200 words or less."
    )
    response = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=query)
    ])
    return response.content.strip()

# Summarize research results from Vector DB
# def summarize_research_results(texts, query):
# ---------------------------------------------------------
# Generate a detailed deep research report
# ---------------------------------------------------------
def generate_detailed_report(texts, query):
    """
    Generate a **comprehensive financial research report** for the user.
    This is NOT for educational purposes, but rather a professional-level
    deep research response.
    Do not include any disclaimers or educational content.
    Do not include any date or prepared for prepared by rather it should look like a professional report or long summary.
    """
    context = "\n".join(texts)
    prompt = f"""
    You are a senior financial research analyst tasked with producing a 
    **comprehensive and professional research report** for the query: "{query}".

    Guidelines:
    - Write in a formal and analytical tone suitable for professional investors or executives.
    - Provide deep insights, trends, risks, and opportunities.
    - Support claims with reasoning and contextual analysis.
    - Organize into sections with headings and subheadings.
    - Include key metrics, market dynamics, and possible future implications.
    - Length: at least 2-3 pages equivalent, detailed and thorough.

    Research Context:
    {context}

    Now, draft the full research report.
    """
    response = llm.invoke([
        SystemMessage(content="You are a financial research assistant producing full professional reports."),
        HumanMessage(content=prompt)
    ])
    return response.content.strip()
# Handle general conversation
def general_response(query):
    prompt = f"Respond politely and naturally to: {query}"
    response = llm.invoke([
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content=prompt)
    ])
    return response.content.strip()