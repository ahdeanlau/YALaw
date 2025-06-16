
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Input the the description of the case, the user want to find

# Press the button "Search"

# Display the names of the relevant cases, eg 10 cases

import streamlit as st
from typing import List, Dict
from embeddings.retriever import QdrantQueryRetriever

st.set_page_config(page_title="Case Finder", layout="wide")

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
                "snippet": query_response.points[i].payload.get('court', 'Untitled'),
                "url": query_response.points[i].payload.get('source_html_file', '#'),
                "full_text": query_response.points[i].payload.get('full_text', 'Untitled'),
                "similarity_score": query_response.points[i].score
            }
        )
    return results


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
        * Describe parties, facts, or legal issues succinctly.
        * Use quotation marks for exact phrases.
        * Filter by year or jurisdiction if known.
        """
    )

# --------------------- MAIN LAYOUT -------------------------------------------

st.title("⚖️  Legal Case Finder")

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
        st.session_state["results"] = search_similar_cases(query)
        st.session_state["page"] = 0

results = st.session_state["results"]
page = st.session_state["page"]

# Results list --------------------------------------------------------------
if results:
    total = len(results)
    total_pages = (total - 1) // PAGE_SIZE + 1

    st.markdown(
        f"**Showing page {page + 1} of {total_pages}**  ​{total} "
        f"result{'s' if total != 1 else ''} found"
    )
    st.divider()

    start, end = page * PAGE_SIZE, (page + 1) * PAGE_SIZE
    page_slice = results[start:end]

    for idx, case in enumerate(page_slice, start=1):
        with st.container():
            st.subheader(case["title"], anchor=False)
            st.write(case["snippet"])
            st.markdown(f"**Relevance**: <span style='color:{'green' if case['similarity_score'] > 0.8 else 'orange' if case['similarity_score'] > 0.6 else 'red'}'>{case['similarity_score']:.2f}</span>", unsafe_allow_html=True)

            link_col, dl_col = st.columns([3, 1])
            with link_col:
                st.markdown(f"[🌐 View Source]({case['url']})")
            with dl_col:
                st.download_button(
                    label="⬇️ Download",
                    data=case["full_text"],
                    file_name=f"{case['title'].replace(' ', '_')}.doc",
                    mime="text/plain",
                    key=f"dl-{start + idx}"
                )
            st.divider()

    # Pagination controls --------------------------------------------------
    prev_col, next_col = st.columns(2)
    with prev_col:
        if st.button("⬅️ Previous", disabled=page == 0):
            st.session_state["page"] -= 1
            st.experimental_rerun()
    with next_col:
        if st.button("Next ➡️", disabled=page >= total_pages - 1):
            st.session_state["page"] += 1
            st.experimental_rerun() # TODO: replace with a more efficient rerun
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
