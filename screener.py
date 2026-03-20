import os
import json
import pdfplumber
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an expert technical recruiter with 10+ years of experience. 
Given a job description and a resume, evaluate the candidate strictly, objectively, and fairly.
Always anonymize your internal evaluation — focus on skills, experience, and fit, not personal details."""

USER_PROMPT = """
Job Description:
{jd}

---

Resume Text:
{resume_text}

---

Evaluate this candidate for the role above. Return ONLY valid JSON with no extra text, markdown, or code fences:

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
    """Extract all text from a PDF file."""
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


def screen_resume(jd: str, resume_text: str, filename: str) -> dict:
    """Send a single resume + JD to Claude and return structured evaluation."""
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": USER_PROMPT.format(jd=jd, resume_text=resume_text[:8000])
                }
            ]
        )
        raw = message.content[0].text.strip()
        # Strip markdown fences if present
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


def screen_all_resumes(jd: str, pdf_files: list) -> list:
    """Screen multiple resumes and return sorted results."""
    results = []
    for pdf_path, filename in pdf_files:
        text = extract_text_from_pdf(pdf_path)
        result = screen_resume(jd, text, filename)
        results.append(result)
    # Sort by score descending
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results
