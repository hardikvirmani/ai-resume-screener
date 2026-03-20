import streamlit as st
import pandas as pd
import tempfile
import os
from screener import screen_resume, extract_text_from_pdf

st.set_page_config(page_title="AI Resume Screener", page_icon="🎯", layout="wide")

st.markdown("""
<style>
    .main-title { font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; }
    .subtitle { color: #888; font-size: 1rem; margin-bottom: 2rem; }
    .score-badge { display: inline-block; padding: 4px 14px; border-radius: 20px; font-weight: 600; font-size: 0.9rem; }
    .rec-strong { background: #d1fae5; color: #065f46; }
    .rec-yes    { background: #dbeafe; color: #1e40af; }
    .rec-maybe  { background: #fef3c7; color: #92400e; }
    .rec-no     { background: #fee2e2; color: #991b1b; }
    .section-label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #9ca3af; margin-bottom: 0.3rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🎯 AI Resume Screener</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Paste a job description, upload resumes, and let AI rank your candidates.</div>', unsafe_allow_html=True)

api_key = st.sidebar.text_input("Groq API Key", type="password",
    value=st.secrets.get("GROQ_API_KEY", ""),
    help="Get your free key at console.groq.com")

st.sidebar.markdown("---")
st.sidebar.markdown("**How it works**")
st.sidebar.markdown("1. Enter your job description\n2. Upload one or more resume PDFs\n3. Click **Screen Resumes**\n4. Review ranked results & export")
st.sidebar.markdown("---")
st.sidebar.markdown("⚠️ **Bias notice:** AI screening can reflect training biases. Always have a human review shortlisted candidates.")

col1, col2 = st.columns([1, 1], gap="large")
with col1:
    st.markdown("#### Job Description")
    jd = st.text_area("Paste the full job description here", height=300,
        placeholder="e.g. We're hiring a Python Backend Engineer...")
with col2:
    st.markdown("#### Upload Resumes")
    uploaded_files = st.file_uploader("Upload PDF resumes (multiple allowed)", type=["pdf"], accept_multiple_files=True)
    if uploaded_files:
        st.success(f"{len(uploaded_files)} resume(s) uploaded")
        for f in uploaded_files:
            st.caption(f"📄 {f.name}")

st.markdown("---")
run_col, _ = st.columns([1, 3])
with run_col:
    run = st.button("🚀 Screen Resumes", type="primary", use_container_width=True,
                    disabled=not (jd and uploaded_files and api_key))

if not api_key:
    st.info("Enter your free Groq API key in the sidebar. Get one at console.groq.com")

if run:
    results = []
    progress = st.progress(0, text="Starting screening...")
    for i, uf in enumerate(uploaded_files):
        progress.progress(i / len(uploaded_files), text=f"Screening {uf.name}... ({i+1}/{len(uploaded_files)})")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uf.getbuffer())
            tmp_path = tmp.name
        text = extract_text_from_pdf(tmp_path)
        os.unlink(tmp_path)
        r = screen_resume(jd, text, uf.name, api_key)
        results.append(r)
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    progress.progress(1.0, text="Done!")
    st.session_state["results"] = results

if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]
    st.markdown("## Results")
    total = len(results)
    strong = sum(1 for r in results if "Strong" in r.get("recommendation",""))
    yes    = sum(1 for r in results if r.get("recommendation","") == "Yes")
    maybe  = sum(1 for r in results if r.get("recommendation","") == "Maybe")
    avg_score = round(sum(r.get("score",0) for r in results) / total) if total else 0
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Screened", total)
    m2.metric("Strong Yes", strong)
    m3.metric("Yes / Maybe", f"{yes} / {maybe}")
    m4.metric("Avg Score", f"{avg_score}/100")
    st.markdown("---")
    df = pd.DataFrame([{
        "Rank": i+1, "Name": r.get("name",""), "File": r.get("filename",""),
        "Score": r.get("score",0), "Recommendation": r.get("recommendation",""),
        "Summary": r.get("summary",""), "Strengths": " | ".join(r.get("strengths",[])),
        "Gaps": " | ".join(r.get("gaps",[]))
    } for i, r in enumerate(results)])
    st.download_button("⬇️ Export to CSV", df.to_csv(index=False).encode(),
                       file_name="screening_results.csv", mime="text/csv")
    st.markdown("### Candidate Rankings")
    rec_class = {"Strong Yes": "rec-strong", "Yes": "rec-yes", "Maybe": "rec-maybe", "No": "rec-no", "Error": "rec-no"}
    for i, r in enumerate(results):
        rec = r.get("recommendation", "")
        css = rec_class.get(rec, "rec-maybe")
        score = r.get("score", 0)
        score_color = "#065f46" if score >= 75 else "#1e40af" if score >= 50 else "#92400e" if score >= 30 else "#991b1b"
        with st.expander(f"#{i+1}  {r.get('name','Unknown')}  —  Score: {score}/100  |  {rec}", expanded=(i < 3)):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown('<div class="section-label">Summary</div>', unsafe_allow_html=True)
                st.write(r.get("summary", ""))
                st.markdown('<div class="section-label" style="margin-top:1rem;">Strengths</div>', unsafe_allow_html=True)
                for s in r.get("strengths", []):
                    st.markdown(f"✅ {s}")
                st.markdown('<div class="section-label" style="margin-top:1rem;">Gaps</div>', unsafe_allow_html=True)
                for g in r.get("gaps", []):
                    st.markdown(f"⚠️ {g}")
            with c2:
                st.markdown('<div class="section-label">Score</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:3rem;font-weight:800;color:{score_color};">{score}</div><div style="color:#9ca3af;font-size:0.85rem;">out of 100</div>', unsafe_allow_html=True)
                st.markdown('<div class="section-label" style="margin-top:1rem;">Recommendation</div>', unsafe_allow_html=True)
                st.markdown(f'<span class="score-badge {css}">{rec}</span>', unsafe_allow_html=True)
                st.markdown('<div class="section-label" style="margin-top:1rem;">Source File</div>', unsafe_allow_html=True)
                st.caption(r.get("filename",""))
