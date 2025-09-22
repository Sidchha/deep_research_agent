# utils/web_search.py
import requests
from ddgs import DDGS
from utils.pdf_utils import fetch_pdf_text
from utils.vector_db import add_texts, similarity_search

# -------------------------------
# Helper: Flatten and clean texts
# -------------------------------
def flatten_and_clean_texts(texts):
    """
    Ensure all elements are strings and non-empty.
    If an element is a list or tuple, join it into a single string.
    Remove any empty or whitespace-only strings.
    """
    flattened = []
    for t in texts:
        if isinstance(t, (list, tuple)):
            t = " ".join(str(x) for x in t)
        else:
            t = str(t)
        if t.strip():  # Only keep non-empty strings
            flattened.append(t.strip())
    return flattened

# -------------------------------
# DuckDuckGo Search
# -------------------------------
def duckduckgo_search(query, max_results=20):
    snippets, urls = [], []
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            for r in results:
                snippets.append(r.get("body", ""))
                urls.append(r.get("href", ""))
    except Exception as e:
        print(f"[DuckDuckGo Error] {e}")
    return snippets, urls

# -------------------------------
# Guaranteed Web Search
# -------------------------------
def web_search(query, min_urls=15, num_results=25):
    urls = set()
    results_text = []

    while len(urls) < min_urls:
        snippets, new_urls = duckduckgo_search(query, max_results=num_results)
        for snippet, url in zip(snippets, new_urls):
            if url and url not in urls:
                urls.add(url)
                results_text.append(snippet)

        if len(new_urls) == 0:
            break

    return results_text, list(urls)

# -------------------------------
# Perform Full Deep Research
# -------------------------------
def perform_deep_research(query):
    # 1️⃣ Normal web search
    search_results, urls = web_search(query, min_urls=15)

    # 2️⃣ Extra PDF search
    _, pdf_urls = web_search(f"{query} filetype:pdf", min_urls=5)
    all_urls = list(set(urls + pdf_urls))

    # 3️⃣ Fetch PDF text
    pdf_texts = fetch_pdf_text(all_urls)

    # 4️⃣ Combine all text and clean
    all_texts = list(search_results) + list(pdf_texts)
    all_texts = flatten_and_clean_texts(all_texts)

    if not all_texts:
        print("[Warning] No valid text found for embedding. Returning empty results.")
        return [], all_urls

    # 5️⃣ Store in vector DB and retrieve relevant results
    add_texts(all_texts, metadatas={"query": query})
    relevant_texts = similarity_search(query, k=10)

    return relevant_texts, all_urls
