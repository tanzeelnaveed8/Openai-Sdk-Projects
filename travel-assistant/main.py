import streamlit as st
import asyncio
from agents import Agent, Runner
from connection import config

# ------------------- AGENTS -------------------

destination_agent = Agent(
    name="Destination Agent",
    instructions="""
    You are an expert travel guide assistant. Based on the user's selected country, cities, group type (solo, friends, family), and trip duration, recommend top tourist attractions for each city.

    Focus on:
    - Cultural or historical importance
    - Popularity among travelers
    - Suitability for the selected group type
    - Safety and overall experience

    Format your response in Markdown. Provide the city's name in bold followed by bullet-pointed attractions. Mention why each place is worth visiting in 1 line.

    Example:

    **Paris**
    - Eiffel Tower: Iconic landmark, ideal for panoramic views and photos
    - Louvre Museum: World-renowned museum, perfect for art and history lovers

    **Nice**
    - Promenade des Anglais: Scenic seaside walkway, ideal for families and evening strolls

    Budget or cost details are **not required**.
    """
)



budget_agent = Agent(
    name="Budget Agent",
    instructions="""
    You are a travel budget assistant. Estimate the cost of a trip based **only on local travel** (within the selected country), including transportation between cities, local accommodation, meals, and attractions.

    Never assume international flights unless explicitly mentioned. Use realistic local pricing.

    Format:
    - Local Transport: $...
    - Hotel: $...
    - Food: $...
    - Activities: $...
    - Total: $...
    - Comment: Within/Over Budget + suggestion if over
    """
)

qa_agent = Agent(
    name="Q&A Agent",
    instructions="""
    You are a helpful travel assistant. Answer follow-up questions about the user's planned trip using the provided trip summary and context. Be concise, accurate, and friendly. If you don't know the answer, say so.
    """
)

# ------------------- STREAMLIT CONFIG -------------------

st.set_page_config(page_title="✈️ AI Travel Planner")
st.title("✈️ AI-Powered Travel Planner")

# ------------------- INPUT FORM -------------------

country = st.text_input("🌍 Enter Country")
cities_input = st.text_area("🏙️ List Cities (comma-separated)", placeholder="e.g., Paris, Nice, Lyon")
cities = [c.strip().title() for c in cities_input.split(",") if c.strip()]

travel_type = st.selectbox("👥 Travel Type", ["Solo", "Friends", "Family"])
group_size = 1
if travel_type == "Friends":
    group_size = st.slider("Number of friends", 1, 10, 2)
elif travel_type == "Family":
    group_size = st.slider("Number of family members", 2, 10, 4)

duration = st.slider("📅 Duration (in days)", 1, 30, 5)
budget = st.number_input("💰 Total Budget (USD)", min_value=100)
submit = st.button("🧳 Plan My Trip")

# ------------------- SESSION STATE -------------------

if "trip_summary" not in st.session_state:
    st.session_state.trip_summary = ""
if "trip_done" not in st.session_state:
    st.session_state.trip_done = False
if "qna_list" not in st.session_state:
    st.session_state.qna_list = []

# ------------------- AGENT RUNNER -------------------

async def run_agents():
    user_context = f"""
    Country: {country}
    Cities: {', '.join(cities)}
    Travel Type: {travel_type}
    Group Size: {group_size}
    Trip Duration: {duration} days
    Budget: ${budget}
    """

    dest_response = await Runner.run(
        starting_agent=destination_agent,
        input=[{"role": "user", "content": user_context}],
        run_config=config
    )

    budget_prompt = f"""
    Trip Destinations:\n{dest_response.final_output}
    Country: {country}
    Duration: {duration} days
    Group: {group_size} ({travel_type})
    Budget Limit: ${budget}
    """

    budget_response = await Runner.run(
        starting_agent=budget_agent,
        input=[{"role": "user", "content": budget_prompt}],
        run_config=config
    )

    st.session_state.trip_summary = user_context
    return dest_response.final_output, budget_response.final_output

# ------------------- DISPLAY RESULTS -------------------

if submit:
    if not country or not cities:
        st.warning("Please enter country and at least one city.")
    else:
        with st.spinner("Planning your trip with agents..."):
            dest_out, budget_out = asyncio.run(run_agents())
            st.session_state.trip_done = True
            st.session_state.dest_out = dest_out
            st.session_state.budget_out = budget_out

# ------------------- SHOW PLANNED TRIP IF EXISTS -------------------

if st.session_state.trip_done:
    st.subheader("📋 Trip Summary")
    st.markdown(st.session_state.trip_summary)

    st.subheader("📍 Recommended Attractions")
    st.markdown(st.session_state.dest_out)

    st.subheader("💰 Estimated Budget")
    st.markdown(st.session_state.budget_out)

# ------------------- FOLLOW-UP QUESTIONS -------------------

if st.session_state.trip_done:
    st.subheader("🤔 Got more questions about your trip?")
    follow_up = st.text_input("Ask a follow-up question about your plan...")

    if follow_up:
        with st.spinner("Thinking..."):
            async def answer_question():
                return await Runner.run(
                    starting_agent=qa_agent,
                    input=[{
                        "role": "user",
                        "content": f"{follow_up}\n\nTrip Info:\n{st.session_state.trip_summary}"
                    }],
                    run_config=config
                )

            followup_result = asyncio.run(answer_question())
            st.session_state.qna_list.append((follow_up, followup_result.final_output))

    if st.session_state.qna_list:
        st.subheader("💬 Follow-up Answers")
        for q, a in st.session_state.qna_list:
            st.markdown(f"**Q:** {q}")
            st.markdown(f"**A:** {a}")
            st.markdown("---")
