# YALeDoc - Your AI Legal Document Generator
## TYPE OF LEGAL DOCUMENTS

# What is the type of legal documents?
# - divorce Joint petition
# - contract
# - NDA
# - patent
# - employment
# - loan
# - rental
# - will
# - small-claims

## ASK QUESTIONS FOR DETAILS

# For example divorce, continue to ask the below for more context:
# - custody
# - alimony
# - visitation
# - division of property
# - child support
# - spousal support
# - mediation
# - arbitration
# - collaborative divorce
# - litigation
# - separation agreement
# - divorce decree
# - divorce settlement
# - divorce mediation
# - divorce arbitration
# - divorce collaborative law

# The above applies to other types of legal documents as well.


# Compile into a single prompt

# Retrieve templates and relevant legal documents (in Malaysia) from Qdrant VectorDB.
# (Optional) Use user's uploaded documents as context if provided.

# Compile into a single prompt, with documents as context.

# Send to OpenAI API for completion.

# Print the response for user, able to download as word or PDF.

# Else, accept extra information from user, and repeat the process to refine the agreeement.

"""Streamlit app – YA Legal Document Generator (YALeDoc)"""

import streamlit as st
import io
from typing import Dict, List

try:
    from docx import Document  # python-docx
except ImportError:
    Document = None

try:
    from reportlab.pdfgen import canvas  # reportlab
except ImportError:
    canvas = None

st.set_page_config(page_title="YALeDoc – AI Legal Document Generator", layout="centered")

# -----------------------------------------------------------------------------
# Mock backend functions  – replace with real implementations
# -----------------------------------------------------------------------------

def mock_fetch_questions(doc_type: str) -> List[str]:
    """Return a list of follow‑up questions for the selected doc type."""
    qa_bank = {
        "divorce Joint petition": [
            "Custody arrangements?",
            "Alimony terms?",
            "Visitation schedule?",
            "Division of property details?",
            "Child support amount?",
            "Spousal support details?",
            "Preferred dispute‑resolution method (mediation / arbitration / collaborative)?",
            "Any existing separation agreement?",
        ],
        "contract": [
            "Parties involved?",
            "Subject matter of the contract?",
            "Start and end date?",
            "Payment terms?",
            "Governing law?",
        ],
        "NDA": [
            "Disclosing vs. receiving parties?",
            "Scope of confidential information?",
            "Duration of confidentiality?",
            "Jurisdiction?",
        ],
        "patent": [
            "Patent type (utility/design)?",
            "Inventor details?",
            "Title of invention?",
            "Priority claim?",
        ],
        "employment": [
            "Position title?",
            "Salary & benefits?",
            "Probation period?",
            "Notice period?",
        ],
        "loan": [
            "Lender and borrower names?",
            "Principal amount?",
            "Interest rate?",
            "Repayment schedule?",
        ],
        "rental": [
            "Property address?",
            "Rent amount & frequency?",
            "Lease term?",
            "Security deposit?",
        ],
        "will": [
            "Testator full name?",
            "Beneficiaries & shares?",
            "Executor name?",
            "Guardians for minors?",
        ],
        "small-claims": [
            "Plaintiff & defendant?",
            "Amount in dispute?",
            "Cause of action?",
            "Evidence summary?",
        ],
    }
    return qa_bank.get(doc_type, [])


def mock_generate_document(prompt: str) -> str:
    """Fake call to OpenAI – returns a canned response."""
    return (
        "<DRAFT OUTPUT>\n\n" + prompt + "\n\n<END OF DRAFT>"  # Replace with real completion
    )

# -----------------------------------------------------------------------------
# Helpers for download files
# -----------------------------------------------------------------------------

def _create_docx(text: str) -> io.BytesIO:
    buffer = io.BytesIO()
    if Document is None:
        buffer.write(text.encode("utf-8"))
    else:
        doc = Document()
        for para in text.split("\n"):
            doc.add_paragraph(para)
        doc.save(buffer)
    buffer.seek(0)
    return buffer


def _create_pdf(text: str) -> io.BytesIO:
    buffer = io.BytesIO()
    if canvas is None:
        buffer.write(text.encode("utf-8"))
    else:
        pdf = canvas.Canvas(buffer)
        width, height = pdf._pagesize
        y = height - 72
        for line in text.split("\n"):
            pdf.drawString(72, y, line)
            y -= 14
            if y < 72:
                pdf.showPage()
                y = height - 72
        pdf.save()
    buffer.seek(0)
    return buffer

# -----------------------------------------------------------------------------
# Custom CSS
# -----------------------------------------------------------------------------

st.markdown(
    """
    <style>
    .question-box {
        background: #f7f8fa;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dde1e6;
    }
    .answer-box input {
        background: #ffffff !important;
    }
    .refine-box {
        border: 1px dashed #adb5bd;
        border-radius: 0.5rem;
        padding: 0.75rem;
        background: #fcfcfd;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# SESSION STATE
# -----------------------------------------------------------------------------

if "doc_type" not in st.session_state:
    st.session_state["doc_type"] = ""
if "answers" not in st.session_state:
    st.session_state["answers"] = {}
if "generated" not in st.session_state:
    st.session_state["generated"] = ""
if "extra" not in st.session_state:
    st.session_state["extra"] = ""

# -----------------------------------------------------------------------------
# UI – Step 1: Choose document type
# -----------------------------------------------------------------------------

st.header("📝 YALeDoc – AI Legal Document Generator")

doc_type = st.selectbox(
    "What type of legal document do you need?",
    [
        "divorce Joint petition",
        "contract",
        "NDA",
        "patent",
        "employment",
        "loan",
        "rental",
        "will",
        "small-claims",
    ],
    index=0 if not st.session_state["doc_type"] else None,
)

if doc_type != st.session_state.get("doc_type"):
    # reset when user chooses a new type
    st.session_state["doc_type"] = doc_type
    st.session_state["answers"] = {}
    st.session_state["generated"] = ""
    st.session_state["extra"] = ""

# -----------------------------------------------------------------------------
# UI – Step 2: Gather details dynamically
# -----------------------------------------------------------------------------

st.subheader("Provide details 📋")
questions = mock_fetch_questions(doc_type)

with st.form("details_form"):
    for q in questions:
        default_val = st.session_state["answers"].get(q, "")
        response = st.text_input(q, default_val, key=q)
        st.session_state["answers"][q] = response

    uploaded_files = st.file_uploader(
        "Optional: upload reference documents (PDF, DOCX, TXT)",
        accept_multiple_files=True,
    )

    submitted = st.form_submit_button("Compile & Generate draft 👉")

if submitted:
    with st.spinner("Generating draft…"):
        # Build prompt ---------------------------------------------------------
        prompt_parts = [f"Document type: {doc_type}"]
        for q, ans in st.session_state["answers"].items():
            prompt_parts.append(f"{q} {ans}")
        if uploaded_files:
            prompt_parts.append("User uploaded docs provided as additional context.")
        if st.session_state["extra"]:
            prompt_parts.append("Additional user info: " + st.session_state["extra"])
        full_prompt = "\n".join(prompt_parts)

        st.session_state["generated"] = mock_generate_document(full_prompt)

# -----------------------------------------------------------------------------
# UI – Step 3: Display & downloads
# -----------------------------------------------------------------------------

if st.session_state["generated"]:
    st.subheader("Draft document ✨")
    st.code(st.session_state["generated"], language="markdown")

    col1, col2 = st.columns(2)
    with col1:
        docx_file = _create_docx(st.session_state["generated"])
        st.download_button(
            "💾 Download DOCX",
            data=docx_file,
            file_name=f"{doc_type.replace(' ', '_')}_draft.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="dl_docx",
        )
    with col2:
        pdf_file = _create_pdf(st.session_state["generated"])
        st.download_button(
            "💾 Download PDF",
            data=pdf_file,
            file_name=f"{doc_type.replace(' ', '_')}_draft.pdf",
            mime="application/pdf",
            key="dl_pdf",
        )

    st.divider()

    # Refinement --------------------------------------------------------------
    st.markdown("#### Add more information or corrections 🛠️")
    extra_info = st.text_area(
        "Enter any additional clauses, corrections, or background to refine the draft.",
        value=st.session_state["extra"],
        height=120,
    )
    if st.button("🔄 Refine draft"):
        st.session_state["extra"] = extra_info
        # Re‑run generation with extra info
        st.session_state["generated"] = ""  # trigger fresh generate on rerun
        st.experimental_rerun()

else:
    st.info("Fill in the details above, then click *Compile & Generate draft*.")

