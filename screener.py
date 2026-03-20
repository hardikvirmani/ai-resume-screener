import os
import json
import pdfplumber
from groq import Groq

SYSTEM_PROMPT = """You are an expert technical recruiter with 10+ years of experience. 
Given a job description and a resume, evaluate the candidate strictly, objectively, and fairly.
Focus on skills, experience, and role fit only."""

USER_PROMPT = """
Job Description:
{jd}

---

Resume Text:
{resume_text}

---

Evaluate this candidate. Return ONLY valid JSON with no extra text or markdown:

{{
  "name": "candidate full name, or 'Unknown' if not found",
  "score": <integer 0-100>,
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "gaps": ["gap 1", "gap 2"],
  "recommendation": "Strong Yes / Yes / Maybe / No",
  "summary": "2-sentence overall assessment of fit for this specific role"
}}
"""

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        text = f"[Error reading PDF: {e}]"
    return text.strip()


def screen_resume(jd: str, resume_text: str, filename: str, api_key: str) -> dict:
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT.format(
                    jd=jd, resume_text=resume_text[:6000]
                )}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
        result["filename"] = filename
        return result
    except Exception as e:
        return {
            "name": filename,
            "filename": filename,
            "score": 0,
            "strengths": [],
            "gaps": [f"Error processing resume: {e}"],
            "recommendation": "Error",
            "summary": "Could not process this resume."
        }


def screen_all_resumes(jd: str, pdf_files: list, api_key: str) -> list:
    results = []
    for pdf_path, filename in pdf_files:
        text = extract_text_from_pdf(pdf_path)
        result = screen_resume(jd, text, filename, api_key)
        results.append(result)
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results
