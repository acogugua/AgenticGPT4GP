#Streamlit UI integration with full agentic AI code by Clement Ogugua Asogwa
"""
complete Streamlit app that uses your full Agentic AI extension with guideline-aware recommendations code, adds branding (colors, fonts), and includes a landing page with a brief intro.

See the video in LinkedIn for this demo. 

***This is a practical project, sensitive/all private information have been removed!
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
    Specify URL of guideline sources
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
# Guideline-aware agent: web fetching 
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

# --------------------------------
# Streamlit layout: Tabs
# --------------------------------

# Initialize placeholders for outputs


# --------------------------------
# Processing pipeline on button click
# --------------------------------

# --------------------------------
# Results tab
# --------------------------------


 # Download buttons
        
    
# --------------------------------
# Guidelines tab
# --------------------------------

# --------------------------------
# Recommendations tab
# --------------------------------")

