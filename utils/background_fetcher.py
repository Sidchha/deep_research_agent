# background_fetcher.py
import time
from utils.web_search import web_search
from utils.pdf_utils import fetch_pdf_text
from utils.stock_utils import fetch_stock_data
from utils.vector_db import add_texts

TRACKED_QUERIES = ["IT Sector 2025", "Pharma 2025", "NASDAQ Top Stocks 2025"]

def background_research_loop(interval=3600):
    while True:
        for query in TRACKED_QUERIES:
            try:
                search_results, urls = web_search(query, num_results=30)
                pdf_texts = fetch_pdf_text(urls)
                api_text = fetch_stock_data(query)
                all_texts = search_results + pdf_texts + [api_text]
                add_texts(all_texts, metadatas={"query": query})
            except:
                continue
        time.sleep(interval)
