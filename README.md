# 🎯 AI Resume Screener

An AI-powered resume screening tool built for the Nutrabay AI Automation Intern assessment.
Upload a job description and multiple PDF resumes — the system scores, ranks, and explains each candidate in seconds.

---

## Live Demo

> Run locally in under 2 minutes (see setup below).  
> Or deploy free on [Streamlit Community Cloud](https://streamlit.io/cloud).

---

## Features

- 📄 **Batch PDF parsing** — upload any number of resumes at once
- 🤖 **LLM-powered evaluation** — Claude scores each candidate 0–100 with reasoning
- 📊 **Ranked leaderboard** — instantly see your top candidates
- 💬 **Explainable AI** — strengths, gaps, and a plain-English summary per candidate
- ⬇️ **CSV export** — share results with your hiring team
- ⚠️ **Bias-aware design** — names are not used in scoring; bias notice is prominently displayed

---

## Setup

```bash
# 1. Clone / download this folder
cd nutrabay_screener

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

You'll need a free [Anthropic API key](https://console.anthropic.com) — enter it in the sidebar.

---

## How It Works

### Architecture

```
resumes (PDF uploads)
       │
       ▼
 pdfplumber → raw text
       │
       ▼
 Claude API (claude-sonnet)
   - System: expert recruiter persona
   - User: JD + resume text
   - Output: structured JSON
       │
       ▼
 Streamlit UI → ranked table + per-candidate breakdown
                           │
                           ▼
                      CSV export
```

### The Core Prompt

The LLM is instructed to return structured JSON with:
- `score` (0–100)
- `strengths` (3 bullet points)
- `gaps` (2 bullet points)  
- `recommendation` (Strong Yes / Yes / Maybe / No)
- `summary` (2-sentence plain English)

Prompting the model to focus on skills and experience — not personal identifiers — reduces demographic bias in evaluation.

---

## Tools & Technologies

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Anthropic Claude API | LLM-based resume evaluation |
| pdfplumber | PDF text extraction |
| Streamlit | Web UI (no frontend code needed) |
| pandas | Results table + CSV export |

---

## Bias & Ethics Notice

AI resume screening can inadvertently replicate biases present in historical hiring data or training corpora. This tool mitigates this by:

1. **Skills-first prompting** — the LLM is instructed to evaluate skills, experience, and role fit, not personal attributes.
2. **Transparent reasoning** — every score comes with explicit strengths and gaps, so a human reviewer can validate or override it.
3. **Human-in-the-loop** — the tool is designed as a *shortlisting aid*, not a final decision-maker. The UI prominently reminds users to have a human review all shortlisted candidates.

In a production deployment, additional mitigations would include: name/gender anonymization before scoring, regular audits of score distributions across demographic groups, and clear documentation for hiring managers.

---

## Possible Extensions

- [ ] Add monthly email digest of pipeline stats
- [ ] Integrate with Google Sheets / ATS via webhook
- [ ] Support `.docx` resumes in addition to PDFs
- [ ] Add a "ask follow-up questions" chat interface per candidate
- [ ] Self-hosted model option (Ollama) for privacy-sensitive orgs
