import streamlit as st
import threading

from utils.llm_utils import (
    classify_query_dynamic,
    generate_research_plan,
    generate_detailed_report,
    general_response,
)
from utils.web_search import perform_deep_research
from utils.stock_utils import fetch_stock_data
from utils.vector_db import add_texts

st.set_page_config(page_title="Financial Research Agent", layout="wide")
st.title("💹 Financial & Sector Research Agent")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_research" not in st.session_state:
    st.session_state.pending_research = None

# Background thread placeholder
if "background_thread_started" not in st.session_state:
    def dummy_background_loop(interval):
        while True:
            import time
            time.sleep(interval)
    t = threading.Thread(target=dummy_background_loop, args=(3600,), daemon=True)
    t.start()
    st.session_state.background_thread_started = True

# User input
user_query = st.chat_input("Enter your query:")

if user_query:
    st.session_state.chat_history.append({"role": "user", "content": user_query})

    with st.spinner("Analyzing query... ⏳"):
        category_json = classify_query_dynamic(user_query)

        if "Out-of-Scope" in category_json:
            response_text = general_response(user_query)
            st.session_state.chat_history.append({"role": "assistant", "content": response_text})
        else:
            research_plan = generate_research_plan(user_query)
            st.session_state.pending_research = {"query": user_query, "plan": research_plan}

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Proposed research plan:\n\n{research_plan}\n\nProceed with deep research? (Yes / No)"
            })

# Confirmation buttons
if st.session_state.pending_research:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, proceed"):
            with st.spinner("Conducting deep research... 🔎"):
                query = st.session_state.pending_research["query"]
                relevant_texts, urls = perform_deep_research(query)
                stock_data = fetch_stock_data(query)
                if stock_data:
                    relevant_texts.append(stock_data)

                add_texts(relevant_texts, metadatas={"query": query})
                report = generate_detailed_report(relevant_texts, query)

                final_response = f"**Research Plan:**\n{st.session_state.pending_research['plan']}\n\n"
                final_response += f"**Detailed Report:**\n{report}\n\n"
                final_response += "**Sources:**\n" + "\n".join(urls) if urls else "Sources: Web search and APIs"

                st.session_state.chat_history.append({"role": "assistant", "content": final_response})
                st.session_state.pending_research = None

    with col2:
        if st.button("❌ No, skip research"):
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "Research skipped. You can ask another query."
            })
            st.session_state.pending_research = None

# Render chat
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])
