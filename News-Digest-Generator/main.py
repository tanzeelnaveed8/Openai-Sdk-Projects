import streamlit as st
import asyncio
from agents import Agent, Runner
from connection import config

# ---------- AGENTS ----------
search_agent = Agent(
    name="Search Agent",
    instructions="""
You are an intelligent news search assistant.

Given a user topic, your task is to find 3–5 recent news articles (from the last 7 days) that are directly related to the topic.

Use any internal tools or web search capabilities available to retrieve real articles.

Return the result as a structured list in JSON format with the following fields:
- title
- summary or content
- source (e.g., BBC, Reuters)
- publication date (ISO format: YYYY-MM-DD)

Do not explain what you're doing — only return the JSON list of articles.
"""
)
filter_agent = Agent(
    name="Filter Agent",
    instructions="""
You are a filtering agent for news content.

Your task is to review the list of articles provided by the Search Agent and filter out:
- Any articles older than 7 days.
- Any articles from unknown or unreliable sources.

Return only high-quality, recent articles in the same structured JSON format as received.

Do not include explanations. Only return the filtered JSON.
"""
)


digest_agent = Agent(
    name="Digest Agent",
    instructions="""
Your task is to summarize each article in one concise sentence.
Include the article title, the main point, and the source.
Return a markdown-formatted digest with 3–5 bullet points.

Only return the final digest in markdown. Do not explain what you're going to do.
"""
)

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="📰 News Digest Generator", layout="centered")
st.title("📰 News Digest Generator")
st.caption("Get quick daily summaries from trusted sources.")

# ---------- USER INPUT ----------
with st.form("news_form"):
    topic = st.text_input("🔍 Enter a topic (e.g., AI, Sports):")
    submitted = st.form_submit_button("Generate Digest")

# ---------- AGENT FLOW ----------
async def handle_news_digest(topic):
    search_response = await Runner.run(
        starting_agent=search_agent,
        input=[{"role": "user", "content": topic}],
        run_config=config,
    )

    filter_response = await Runner.run(
        starting_agent=filter_agent,
        input=[{"role": "user", "content": search_response.final_output}],
        run_config=config,
    )

    digest_response = await Runner.run(
        starting_agent=digest_agent,
        input=[{"role": "user", "content": filter_response.final_output}],
        run_config=config,
    )

    return digest_response.final_output

# ---------- RUN ----------
if submitted:
    if not topic.strip():
        st.warning("⚠️ Please enter a valid topic.")
    else:
        with st.spinner("Fetching your personalized news digest..."):
            result = asyncio.run(handle_news_digest(topic))
            st.success("✅ News Digest:")
            st.markdown(result)
