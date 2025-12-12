# AgenticGPT4GP: Multi-System Referral & Agentic Triage Assistant
This project delivers a production‑ready clinical triage assistant that ingests GP referral letters in multiple formats (PDF, DOCX, TXT, and images via OCR). 
It automatically summarizes the content, classifies urgency across specialties, and generates actionable recommendations for clinicians.

Built on Large Language Models (LLMs), the system combines retrieval‑augmented generation (RAG) with agentic AI orchestration to produce explainable, guideline‑aware outputs. 
Each stage of the workflow is transparent:

File ingestion handles diverse input formats.

Summarization & Q&A provide concise context and answers.

Multi‑system triage logic applies rule‑based urgency classification.

Guideline highlights are fetched from curated sources such as RACGP and ACEM.

Agentic recommendations synthesize next steps with rationale.

User interface presents results clearly and allows export.

The assistant is designed to support clinicians by streamlining referral review and triage decisions. It supports outputs by grounding recommendations in trusted guidelines. The modular design makes it extensible: guideline sources are extracted from local HealthPathways or institutional standards, and triage rules can be adapted to different specialties. Most of the triage logic here were crafted with consultations with specialist physicians.

Privacy and security are considered throughout, therefore this app is made private and the details of the project and the codes are available only on request. Keys are managed via environment variables, and guideline sources are curated rather than scraped indiscriminately. I developed two versions of this project using Langchain with actual referral and xray reports. This particular system is lightweight, relying on Python libraries (python-docx, PyMuPDF, pytesseract, Pillow, requests, BeautifulSoup, gradio/streamlit) and the OpenAI client for LLM integration. 

By combining structured triage rules with generative AI, GPT4GP demonstrates how agentic AI can deliver practical, guideline‑aware care pathways. It is intended as a proof‑of‑concept for clinical decision support, not a substitute for professional judgment. Clinicians remain in control, with the assistant providing summaries, highlights, and recommendations to accelerate safe, evidence‑based triage.
For more information please contact acogugua@yahoo.com or acogugua1@gmail.com
