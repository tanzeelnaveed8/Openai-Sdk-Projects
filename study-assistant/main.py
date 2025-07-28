import streamlit as st
import asyncio
import re
from agents import Agent, Runner
from connection import config
import fitz  # PyMuPDF
from datetime import date

# ---------- AGENTS ----------
scheduler_agent = Agent(
    name="Study Scheduler",
    instructions="""
Tum ek intelligent study planner ho. User tumhe ek raw text (notes ya PDF content) aur deadline dega.
Tum is text se important topics aur subtopics identify karo.
Fir unke basis par ek daily study plan banao jo deadline ke andar complete ho jaye.

Format:
Day 1: Topic/Subtopic
- [Resource Title](https://example.com)
Day 2: ...
""",
)

research_agent = Agent(
    name="Web Researcher",
    instructions="""
Tumhare paas topic hoga, tum uske liye 3-5 trusted online resources dhundo (Coursera, Google ML, FastAI, Kaggle, etc).
Sirf academic ya trusted sources ke links do. Non-academic ya promotional sites ko exclude karo.

Output markdown format mein do:
- [Resource Title](https://url)
""",
)

summarizer_agent = Agent(
    name="Content Summarizer",
    instructions="""
Tum research content ko summarize karo concise academic tone mein.
Maximum 100 words mein output do.
""",
)

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="📚 Study Assistant", layout="centered")

with st.container():
    st.markdown("## 📚 Personal Study Assistant")
    st.caption("AI-powered tool to build a study plan from your topic or PDF notes.")

# ---------- INPUT SECTION ----------
with st.form("study_form"):
    topic = st.text_input("📌 Topic (optional if uploading PDF):")
    deadline = st.date_input("⏰ Deadline", value=date.today())
    uploaded_pdf = st.file_uploader("📎 Upload PDF Notes (optional)", type="pdf")
    submitted = st.form_submit_button("📅 Generate Study Plan")

# ---------- UTILITY FUNCTIONS ----------
def extract_text_from_pdf(uploaded_file):
    pdf_reader = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    return "\n".join(page.get_text() for page in pdf_reader).strip()

async def run_agents_with_text(raw_text):
    user_prompt = f"Yeh notes hai:\n{raw_text}\nDeadline: {deadline}"

    plan = await Runner.run(
        starting_agent=scheduler_agent,
        input=[{"role": "user", "content": user_prompt}],
        run_config=config,
    )
    research = await Runner.run(
        starting_agent=research_agent,
        input=[{"role": "user", "content": raw_text[:200]}],
        run_config=config,
    )
    summary = await Runner.run(
        starting_agent=summarizer_agent,
        input=[{"role": "user", "content": research.final_output}],
        run_config=config,
    )
    return plan.final_output, research.final_output, summary.final_output

async def run_agents_with_topic(topic_text):
    user_prompt = f"Topic: {topic_text}\nDeadline: {deadline}"

    plan = await Runner.run(
        starting_agent=scheduler_agent,
        input=[{"role": "user", "content": user_prompt}],
        run_config=config,
    )
    research = await Runner.run(
        starting_agent=research_agent,
        input=[{"role": "user", "content": topic_text}],
        run_config=config,
    )
    summary = await Runner.run(
        starting_agent=summarizer_agent,
        input=[{"role": "user", "content": research.final_output}],
        run_config=config,
    )
    return plan.final_output, research.final_output, summary.final_output

# ---------- OUTPUT SECTION ----------
if submitted:
    if uploaded_pdf:
        with st.spinner("🔍 Reading PDF and generating your study plan..."):
            extracted = extract_text_from_pdf(uploaded_pdf)
            plan, research, summary = asyncio.run(run_agents_with_text(extracted))

        st.success("✅ Study Plan Created from PDF!")

        with st.expander("📅 Study Plan"):
            st.markdown(plan)

        with st.expander("🔗 Useful Resources"):
            links = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', research)
            for title, url in links:
                st.markdown(f"- [{title}]({url})")

        with st.expander("📄 PDF Summary"):
            st.markdown(summary)

    elif topic.strip():
        with st.spinner("🧠 Analyzing topic and generating your study plan..."):
            plan, research, summary = asyncio.run(run_agents_with_topic(topic))

        st.success("✅ Study Plan Created from Topic!")

        with st.expander("📅 Study Plan"):
            st.markdown(plan)

        with st.expander("🔗 Useful Resources"):
            links = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', research)
            for title, url in links:
                st.markdown(f"- [{title}]({url})")

        with st.expander("🧠 Summary"):
            st.markdown(summary)
    else:
        st.error("⚠️ Topic ya PDF dena zaroori hai.")
