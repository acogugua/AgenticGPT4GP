#Streamlit UI integration with full agentic AI code by Clement Ogugua Asogwa
"""
complete Streamlit app that uses your full Agentic AI extension with guideline-aware recommendations code, adds branding (colors, fonts), and includes a landing page with a brief intro.
It replaces the Gradio UI with Streamlit tabs while keeping all your original logic intact.
"""

# GPT4GP: Multi-System Referral & Agentic Triage Assistant (Guideline-aware) - Streamlit UI
import os
import tempfile
import re
import requests
import streamlit as st
from bs4 import BeautifulSoup

import docx
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

import openai
from openai import OpenAI
client = OpenAI()  #  reads OPENAI_API_KEY from environment




# --------------------------------
# OpenAI client setup (use env var)
# --------------------------------
# NOTE: Prefer environment variable for security:
#   Windows (PowerShell): setx OPENAI_API_KEY "sk-..."
#   macOS/Linux: export OPENAI_API_KEY="sk-..."
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --------------------------------
# Branding / Custom CSS
# --------------------------------
st.set_page_config(
    page_title="GPT4GP: Multi-System Referral & Agentic Triage Assistant",
    page_icon=" ",  # path to your logo file
    layout="wide"
)


st.markdown("""
    <style>
    /* Global */
    html, body, [class*="css"]  {
        font-family: 'Segoe UI', system-ui, -apple-system, Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Liberation Sans', sans-serif;
        background-color: #f7f9fc;
    }
    /* Headings */
    h1, h2, h3 {
        color: #0a3d62;
        font-weight: 650;
    }
    /* Buttons */
    .stButton>button {
        background-color: #0a3d62;
        color: #ffffff;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        border: 0px;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #1b5fa7;
        color: #ffffff;
        border: 0px;
    }
    /* Cards look */
    .card {
        background: #ffffff;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.06);
        margin-bottom: 16px;
        border: 1px solid #eef2f7;
    }
    /* Tabs */
    [data-baseweb="tab"] {
        font-weight: 600;
    }
    /* Emojis size fix */
    .emoji {
        font-size: 1.1em;
    }
    </style>
""", unsafe_allow_html=True)

# --------------------------------
# Landing page / Intro
# --------------------------------
st.title(" GPT4GP: Multi-System Referral & Agentic Triage Assistant")


st.markdown("""
This production-ready assistant ingests GP referral letters (DOCX, PDF, TXT, image OCR), summarizes them, performs multi-system triage, fetches guideline highlights, and synthesizes **agentic recommendations**.

Workflow:
-  Ingestion →  Summarization →  Triage →  Guideline highlights →  Agentic recommendations →  Export
""")
st.divider()

# --------------------------------
# Configuration (from your code)
# --------------------------------
GUIDELINE_SOURCES = [
    "https://www.racgp.org.au/running-a-practice/practice-standards/standards-5th-edition/standards-for-general-practices-5th-ed/general-practice-standards/gp-standard-1",
    "https://acem.org.au/getmedia/51dc74f7-9ff0-42ce-872a-0437f3db640a/G24_04_Guidelines_on_Implementation_of_ATS_Jul-16.aspx",
    "https://www.clinicalexcellence.qld.gov.au/improvement-exchange/clinical-prioritisation-criteria-cpc-making-triage-everyones-business",
    "https://cesphn.org.au/wp-content/uploads/All_Categories/Practice_Support/20220309_Triage_Chart__1_.pdf",
]

# --------------------------------
# File ingestion (full functions from your code)
# --------------------------------
def read_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def read_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def read_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def read_image(file_path):
    image = Image.open(file_path)
    return pytesseract.image_to_string(image)

def ingest_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".docx":
        return read_docx(file_path)
    elif ext == ".pdf":
        return read_pdf(file_path)
    elif ext == ".txt":
        return read_txt(file_path)
    elif ext in [".png", ".jpg", ".jpeg"]:
        return read_image(file_path)
    else:
        raise ValueError("Unsupported file type")

# --------------------------------
# GPT summarization and Q&A (full from your code)
# --------------------------------
def summarize_text(text):
    prompt = f"Summarize the following GP referral letter succinctly:\n\n{text}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=120
    )
    return response.choices[0].message.content.strip()

def answer_question(question, context):
    prompt = f"Referral letter:\n{context}\n\nAnswer concisely:\nQuestion: {question}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=180
    )
    return response.choices[0].message.content.strip()

# --------------------------------
# Multi-system triage logic (full from your code)
# --------------------------------
def triage_multisystem(summary: str):
    summary = summary.lower()

    triage_rules = {
        # Cardiology
        "Urgent - Cardiology": ["chest pain", "shortness of breath", "heart attack", "unstable angina"],
        "Semi-Urgent - Cardiology": ["ischaemic heart disease", "atrial fibrillation", "hypertension uncontrolled"],
        "Routine - Cardiology": ["high blood pressure", "cholesterol"],

        # Orthopedics
        "Urgent - Orthopedics": ["fracture", "severe pain", "avascular necrosis", "obliterated joint space"],
        "Semi-Urgent - Orthopedics": ["osteoarthritis", "hip pain", "joint space narrowing", "femoro-acetabular impingement"],
        "Routine - Orthopedics": ["mild stiffness", "early osteoarthritis"],

        # Neurology
        "Urgent - Neurology": ["stroke", "seizure", "head trauma", "sudden weakness", "loss of consciousness"],
        "Semi-Urgent - Neurology": [
            "intermittent numbness", "tingling in the leg", "occasional imbalance", "mild weakness",
            "radiculopathy", "nerve compression", "lumbar degenerative changes"
        ],
        "Routine - Neurology": ["tension headache", "mild neuropathy", "stable parkinson's disease"],

        # General medicine fallback
        "Urgent - General Medicine": ["sepsis", "acute infection"],
        "Routine - General Medicine": ["fatigue", "check-up"]
    }

    priorities = ["Urgent", "Semi-Urgent", "Routine"]
    primary_category = None
    secondary_alerts = []

    # Determine primary and collect secondary specialty alerts
    for priority in priorities:
        for category, keywords in triage_rules.items():
            if category.startswith(priority):
                if any(kw in summary for kw in keywords):
                    if primary_category is None:
                        primary_category = category
                    else:
                        # Add other specialties as secondary alerts
                        if category.split(" - ")[1] not in primary_category:
                            secondary_alerts.append(category)

    if primary_category is None:
        primary_category = "Routine - General Medicine"

    return primary_category, sorted(set(secondary_alerts))

# --------------------------------
# Guideline-aware agent: web fetching (full from your code)
# --------------------------------
def fetch_guideline_snippets(query_terms, max_sites=4, per_site_snippets=2):
    """
    Lightweight guideline fetcher:
    - Visits curated sources and extracts title and short snippets that match query terms.
    - Returns list of dicts {source, title, snippet, url}.
    """
    results = []
    terms = [t.lower() for t in query_terms if t]
    for url in GUIDELINE_SOURCES[:max_sites]:
        try:
            r = requests.get(url, timeout=8)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")

            # Title extraction
            title = soup.title.get_text(strip=True) if soup.title else "Guideline resource"

            # Text extraction (limit size to keep it fast)
            text_blocks = soup.get_text(separator="\n")
            # Normalize whitespace and limit block length
            clean_text = re.sub(r"\s+", " ", text_blocks).strip()
            # Simple matching of terms and snippet slicing
            matched_snippets = []
            for t in terms:
                idx = clean_text.lower().find(t)
                if idx != -1:
                    start = max(0, idx - 160)
                    end = min(len(clean_text), idx + 160)
                    snippet = clean_text[start:end]
                    matched_snippets.append(snippet)
                if len(matched_snippets) >= per_site_snippets:
                    break

            # If no term matched, get a generic leading snippet
            if not matched_snippets:
                generic = clean_text[:240]
                matched_snippets.append(generic)

            for s in matched_snippets:
                results.append({
                    "source": title,
                    "title": title,
                    "snippet": s.strip(),
                    "url": url
                })
        except Exception:
            # Fail silently, skip site
            continue

    return results

# --------------------------------
# Agentic AI: care pathway synthesis (full from your code)
# --------------------------------
def agentic_recommendations(summary, primary, secondary, guideline_snippets):
    """
    Synthesizes next steps and rationale, grounded with guideline snippets.
    """
    # Prepare a compact guideline appendix
    guideline_text = ""
    for i, g in enumerate(guideline_snippets[:6], start=1):
        guideline_text += f"- [{g['source']}] {g['snippet']} (Source: {g['url']})\n"

    prompt = f"""
Referral summary:
{summary}

Primary triage: {primary}
Secondary alerts: {secondary}

Guideline highlights:
{guideline_text or '- No guideline snippets retrieved.'}

As an agentic clinical assistant, provide:
1. Next-step recommendations (appointment timing windows, conservative measures, investigations).
2. Rationale referencing the guideline highlights above (general guidance, not patient-specific medical advice).
3. A short, structured care pathway summary (Primary specialty focus + Secondary considerations).
Keep it concise, clinical, and practical.
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=320
    )
    return response.choices[0].message.content.strip()

# --------------------------------
# Helper: persist uploaded file to a temp path for ingestion functions
# --------------------------------
def save_uploaded_file_to_temp(uploaded_file) -> str:
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        return tmp.name

# --------------------------------
# Streamlit layout: Tabs
# --------------------------------
tab_upload, tab_results, tab_guidelines, tab_reco = st.tabs(
    [" Upload Referral", " Results", " Guidelines", " Recommendations"]
)

with tab_upload:
    st.subheader("Upload referral letter")
    uploaded_file = st.file_uploader(
        "Choose a file (PDF, DOCX, TXT, PNG, JPG)",
        type=["pdf","docx","txt","png","jpg","jpeg"],
        accept_multiple_files=False,
        help="Supported formats: PDF, DOCX, TXT, and image files (OCR)."
    )
    question = st.text_input("Ask a clinical question", placeholder="e.g. What is the suspected diagnosis?")
    process_btn = st.button("Process referral")

# Initialize placeholders for outputs
summary = None
primary = None
secondary = []
answer = None
guideline_snippets = []
agentic = None

# --------------------------------
# Processing pipeline on button click
# --------------------------------
if process_btn:
    if uploaded_file is None:
        st.error("Please upload a referral file first.")
    else:
        st.success("✅ File uploaded. Processing...")
        temp_path = save_uploaded_file_to_temp(uploaded_file)

        try:
            # Ingest
            text = ingest_file(temp_path)
            # Summarize
            summary = summarize_text(text)
            # Triage
            primary, secondary = triage_multisystem(summary)
            # Q&A
            answer = answer_question(question, text) if question else "No question asked."
            # Guideline fetch (derive terms)
            primary_level = primary.split(" - ")[0]
            primary_specialty = primary.split(" - ")[1]
            query_terms = [
                primary_specialty.lower(),
                primary_level.lower(),
                "triage", "outpatient", "prioritisation", "referral",
                "numbness" if "numbness" in summary.lower() else "",
                "tingling" if "tingling" in summary.lower() else "",
                "imbalance" if "imbalance" in summary.lower() else "",
                "weakness" if "weakness" in summary.lower() else "",
                "osteoarthritis" if "osteoarthritis" in summary.lower() else "",
            ]
            guideline_snippets = fetch_guideline_snippets(query_terms)
            # Agentic synthesis
            agentic = agentic_recommendations(summary, primary, secondary, guideline_snippets)

            st.toast("Processing complete", icon="✅")
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

# --------------------------------
# Results tab
# --------------------------------
with tab_results:
    st.subheader("Summary & Triage")
    if summary:
        st.markdown(f"""
        <div class="card">
        <h3>Summary</h3>
        <p>{summary}</p>
        </div>
        """, unsafe_allow_html=True)

        emoji_map = {"Urgent": "⚠️", "Semi-Urgent": "🟠", "Routine": "🔵"}
        primary_level = primary.split(" - ")[0]
        primary_display = f"{emoji_map.get(primary_level, '🔵')} {primary}"

        st.markdown(f"""
        <div class="card">
        <h3>Triage result</h3>
        <p class="emoji"><strong>Primary:</strong> {primary_display}</p>
        <p><strong>Secondary alerts:</strong> {", ".join(secondary) if secondary else "None"}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
        <h3>Q&A</h3>
        <p>{answer}</p>
        </div>
        """, unsafe_allow_html=True)

        # Download buttons
        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button(
                label="⬇️ Download summary",
                data=summary,
                file_name="summary.txt",
                mime="text/plain"
            )
        with col_b:
            full_report = f"Summary:\n{summary}\n\nTriage:\nPrimary: {primary}\nSecondary: {', '.join(secondary) if secondary else 'None'}\n\nQ&A:\n{answer}\n"
            st.download_button(
                label="⬇️ Download triage report",
                data=full_report,
                file_name="triage_report.txt",
                mime="text/plain"
            )
    else:
        st.info("Process a referral in the Upload tab to view results.")

# --------------------------------
# Guidelines tab
# --------------------------------
with tab_guidelines:
    st.subheader("Guideline highlights")
    if guideline_snippets:
        for g in guideline_snippets[:8]:
            st.markdown(f"""
            <div class="card">
            <strong>{g['title']}</strong><br/>
            {g['snippet']}<br/>
            <a href="{g['url']}" target="_blank">Source</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Guideline highlights will appear after processing a referral.")

# --------------------------------
# Recommendations tab
# --------------------------------
with tab_reco:
    st.subheader("Agentic recommendations")
    if agentic:
        st.markdown(f"""
        <div class="card">
        {agentic}
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="⬇️ Download recommendations",
            data=agentic,
            file_name="recommendations.txt",
            mime="text/plain"
        )
    else:
        st.info("Recommendations will appear after processing a referral.")
