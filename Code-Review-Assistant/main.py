import streamlit as st
import asyncio
import re
from agents import Agent, Runner
from connection import config

# ---------- AGENTS ----------
analyzer_agent = Agent(
    name="Analyzer Agent",
    instructions="""
    You're a code review assistant. Analyze the given code in any programming language and identify issues such as:
    - Syntax errors
    - Poor code structure
    - Bad naming conventions
    - Missing comments or documentation

    Output a structured list of problems you detect.
    """
)

suggestion_agent = Agent(
    name="Suggestion Agent",
    instructions="""
    You receive a list of code issues from the Analyzer Agent.
    For each issue, suggest improvements or fixes in bullet points.
    Provide actionable advice, applicable to the language used.
    """
)

documentation_agent = Agent(
    name="Documentation Agent",
    instructions="""
    Your task is to generate documentation or comments for the given code, regardless of the programming language.
    Include:
    - Function/class/module descriptions
    - Optional README-style summary

    Format the output in markdown.
    """
)

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="🧑‍💻 Code Review Assistant", layout="centered")
st.title("🧑‍💻 Code Review Assistant")
st.caption("Upload a code file and let AI help you review and document it.")

# ---------- FILE UPLOAD ----------
with st.form("code_review_form"):
    uploaded_file = st.file_uploader(
        "📎 Upload Code File",
        type=["py", "js", "java", "cpp", "c", "ts", "tsx", "jsx", "cs", "rb", "go", "rs", "php"]
    )
    submitted = st.form_submit_button("🔍 Review Code")

# ---------- UTILS ----------
def extract_code_text(file):
    return file.read().decode("utf-8")

async def process_code_review(code_text):
    # Step 1: Analyze
    analysis = await Runner.run(
        starting_agent=analyzer_agent,
        input=[{"role": "user", "content": code_text}],
        run_config=config,
    )

    # Step 2: Suggest Improvements
    suggestions = await Runner.run(
        starting_agent=suggestion_agent,
        input=[{"role": "user", "content": analysis.final_output}],
        run_config=config,
    )

    # Step 3: Generate Documentation
    documentation = await Runner.run(
        starting_agent=documentation_agent,
        input=[{"role": "user", "content": code_text}],
        run_config=config,
    )

    return analysis.final_output, suggestions.final_output, documentation.final_output

# ---------- MAIN ----------
if submitted:
    if uploaded_file:
        code_text = extract_code_text(uploaded_file)

        with st.spinner("🤖 Reviewing your code..."):
            analysis, suggestions, documentation = asyncio.run(process_code_review(code_text))

        st.success("✅ Code Review Complete!")

        with st.expander("🕵️ Code Analysis (Issues Found)", expanded=True):
            st.markdown(analysis)

        with st.expander("💡 Suggestions for Improvement", expanded=True):
            st.markdown(suggestions)

        with st.expander("📄 Auto-generated Documentation", expanded=True):
            st.markdown(documentation)

    else:
        st.error("⚠️ Please upload a code file to review.")