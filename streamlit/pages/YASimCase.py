
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Input the the description of the case, the user want to find

# Press the button "Search"

# Display the names of the relevant cases, eg 10 cases

import streamlit as st
from typing import List, Dict
from embeddings.retriever import QdrantQueryRetriever
from embeddings.query_prompt import OpenAIQueryPrompt

st.set_page_config(page_title="Case Finder", layout="wide")

openai = OpenAIQueryPrompt()

# --------------------- BACKEND ------------------------------------------
retriever = QdrantQueryRetriever(collection_name="commonlii_cases")

def search_similar_cases(query: str, num_results: int = 20) -> List[Dict]:
    """
    
    """
    
    query_response = retriever.similarity_search_by_query_with_dense_vector(
        query=query,
        limit=num_results
    )
    
    results = []
    for i in range(0, num_results):
        results.append(
            {
                "id": query_response.points[i].id,
                "title": f"Case {query_response.points[i].id}: {query_response.points[i].payload.get('case_name', 'Untitled')}",
                "court": query_response.points[i].payload.get('court', 'Untitled'),
                "url": query_response.points[i].payload.get('source_html_url', 'http://www.commonlii.org/my/cases/'),
                "full_text": query_response.points[i].payload.get('full_text', 'Untitled'),
                "similarity_score": query_response.points[i].score,
                "decision_date": query_response.points[i].payload.get('decision_date', 'Unknown'),
            }
        )
    return results

def summarize_relevancy(query: str, case: str) -> str:
    explanation = openai.explain_law_case_relavancy(query=query, case=case)
    return f"{explanation}"

# --------------------- SESSION STATE -----------------------------------------

if "results" not in st.session_state:
    st.session_state["results"] = []
if "page" not in st.session_state:
    st.session_state["page"] = 0

PAGE_SIZE = 10

# --------------------- SIDEBAR ------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        ### Tips 🔍
        * Describe the cases you are looking for **using the semantics**.
        * Do not present a collection of disconnected keywords.
        * Instead, provide a coherent sentence to describe the nature of the case.
        * The result is **sorted by relevance**, with the most relevant cases appearing first.
        * Click on **"How is it related?"** to get a summary of how the case relates to your query.
        * Use the **Download** button to save the full text of the case.
        * Use **View Source** to see the original case on CommonLII.
        """
    )

# --------------------- MAIN LAYOUT -------------------------------------------

st.title("⚖️  Legal Case Similarity Search")

st.markdown(
    """
    _Find the most relevant legal cases by describing the dispute or legal question._
    Enter a few keywords below and click **Search**.
    """
)

# Search form --------------------------------------------------------------
with st.form("search_form", clear_on_submit=False):
    query = st.text_input(
        "Describe the case you are looking for",
        placeholder="e.g. breach of contract construction delay Kuala Lumpur"
    )
    submitted = st.form_submit_button("🔎 Search")

    if submitted:
        # Clear previous summaries
        keys_to_delete = [key for key in st.session_state if key.startswith("summarizing_") or key.startswith("summary_result_")]
        for key in keys_to_delete:
            del st.session_state[key]
        
        st.session_state["results"] = search_similar_cases(query)
        st.session_state["page"] = 0

results = st.session_state["results"]
page = st.session_state["page"]

# Results list --------------------------------------------------------------
if results:
    total = len(results)
    total_pages = (total - 1) // PAGE_SIZE + 1

    st.markdown(
        f"**Showing page {page + 1} of {total_pages}**"
        f" -  ​{total} result{'s' if total != 1 else ''} found"
    )
    st.divider()

    start, end = page * PAGE_SIZE, (page + 1) * PAGE_SIZE
    page_slice = results[start:end]

    for idx, case in enumerate(page_slice, start=1):
        with st.container():
            st.subheader(case["title"], anchor=False)
            st.write(f"**Court**: {case["court"]}")
            st.write(f"**Decision Date**: {case["decision_date"]}")
            st.markdown(f"**Relevance**: <span style='color:{'green' if case['similarity_score'] > 0.8 else 'orange' if case['similarity_score'] > 0.6 else 'red'}'>{case['similarity_score']:.2f}</span>", unsafe_allow_html=True)

            link_col, dl_col = st.columns([4, 1])
            with link_col:
                st.markdown(f"[🌐 View Source]({case['url']})")
            with dl_col:
                summary_col, dl_col = st.columns([1, 1])  # Equal width
                with summary_col:
                    if st.button("📝 How is it related?", key=f"summary-{start + idx}"):
                        st.session_state[f"summarizing_{start + idx}"] = True
                        st.session_state[f"summary_result_{start + idx}"] = None
                with dl_col:
                    st.download_button(
                        label="⬇️ Download",
                        data=case["full_text"],
                        file_name=f"{case['title'].replace(' ', '_')}.doc",
                        mime="text/plain",
                        key=f"dl-{start + idx}"
                    )
            if st.session_state.get(f"summarizing_{start + idx}", False):
                with st.expander("Relatedness Summary", expanded=True):
                    if st.session_state.get(f"summary_result_{start + idx}") is None:
                        with st.spinner("Summarizing..."):
                            result = summarize_relevancy(query, case["full_text"])
                            st.session_state[f"summary_result_{start + idx}"] = result
                            st.session_state[f"summarizing_{start + idx}"] = False
                            st.rerun()
                            # Force expander to be open when summary is loaded
                            st.session_state[f"summarizing_{start + idx}"] = False
                    else:
                        st.write(st.session_state[f"summary_result_{start + idx}"])
            elif st.session_state.get(f"summary_result_{start + idx}") is not None:
                with st.expander("Relatedness Summary", expanded=False):
                    st.write(st.session_state[f"summary_result_{start + idx}"])
            st.divider()

    # Pagination controls --------------------------------------------------
    prev_col, next_col = st.columns(2)
    with prev_col:
        if st.button("⬅️ Previous", disabled=page == 0):
            st.session_state["page"] -= 1
            st.rerun()
    with next_col:
        if st.button("Next ➡️", disabled=page >= total_pages - 1):
            st.session_state["page"] += 1
            st.rerun() # TODO: replace with a more efficient rerun
else:
    st.info("Enter a description and click **Search** to view matching cases.")

# --------------------- CUSTOM CSS -------------------------------------------

st.markdown(
    """
    <style>
    /* Tighten subheader spacing */
    h3 { margin-top: 0.25rem; }
    /* Unify divider look */
    hr { margin: 0.75rem 0; }
    /* Full‑width download buttons */
    button[kind="download"] { width: 100%; }
    </style>
    """,
    unsafe_allow_html=True,
)
