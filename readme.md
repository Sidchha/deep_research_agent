Project Overview

    The Financial & Sector Research Agent is an AI-powered assistant designed to conduct deep research on financial topics, companies, stocks, and industries. It leverages web search, PDF extraction, stock data, and advanced LLMs to generate detailed, actionable, and professional research reports.

    Unlike educational summarizers, this agent produces in-depth reports similar to a professional analyst’s work, including structured research plans, insights, and references.

Features

    Deep Research Agent: Performs web and PDF searches to gather relevant data.

    LLM-Powered Analysis: Uses Google Gemini 1.5 Flash model to generate research reports.

    Stock Data Fetching: Retrieves financial and stock-related data for companies.

    Vector Database Integration: Stores and retrieves research content for semantic search.

    Interactive Chat UI: Streamlit-based chat interface for user queries.

    Background Research: Periodic automated updates using a background thread.

    Handles PDF & Web Sources: Extracts text from multiple PDFs and web pages reliably

Notes

    The agent relies on DuckDuckGo for web search and optional PDF links.

    Vector DB (FAISS) is used for semantic retrieval of documents.

    PDF extraction handles multi-page documents, tables, and text content.

    Empty or invalid content is filtered to avoid errors with embeddings.

Future Improvements

    Integrate Google Custom Search API for more accurate results.

    Add multi-language support for global financial reports.

    Enable real-time PDF downloading and caching for large datasets.

    Support additional LLMs or embeddings for faster and richer insights.
