import streamlit as st
import asyncio
import re
from agents import Agent, Runner
from connection import config

# ---------- HARDCODED DATA ----------
faq_data = {
    "iphone availability": "Haan, iPhone currently stock mein available hai.",
    "delivery time for iphone": "Delivery usually 3-5 business days lagti hai.",
    "payment method": "Aap Cash on Delivery, Credit Card, aur EasyPaisa use kar sakte hain."
}

return_policy_data = {
    "return policy": "Product delivery ke 7 din ke andar return kiya ja sakta hai agar seal nahi tooti ho.",
    "refund time": "Refund 5-7 working days mein process hota hai.",
    "exchange possible": "Haan, exchange possible hai within 7 days."
}

# ---------- MANUAL TOOLS ----------
def search_faq(query):
    for key, value in faq_data.items():
        if query.lower() in key:
            return value
    return "Maaf kijiye, mujhe is sawal ka jawab nahi mila FAQ mein."

def search_return_policy(query):
    for key, value in return_policy_data.items():
        if query.lower() in key:
            return value
    return "Return policy mein yeh specific information nahi mili."

# ---------- AGENTS ----------
inquiry_agent = Agent(
    name="Inquiry Agent",
    instructions="""
    Tum ek helpful customer support agent ho. Tumhara kaam user ke general sawalon ka jawab dena hai — jaise delivery time, product availability, payment options, etc.

    Tumhare paas ek `search_faq` function hoga — use karo to verify answers before responding.
    Agar question complicated ho ya unclear ho, to escalate karo Escalation Agent ko with keyword `escalate_to_human`.
    Agar user return se related kuch bole to keyword `escalate_to_returns` bhejo.
    """
)

returns_agent = Agent(
    name="Returns Agent",
    instructions="""
    Tum ek returns specialist ho. User agar return initiate karna chahta hai to tum uski order details maangte ho
    aur return policy ke file se guide karte ho. Agar issue unclear ho to Escalation Agent ko forward karo with keyword `escalate_to_human`.
    """
)

escalation_agent = Agent(
    name="Escalation Agent",
    instructions="""
    Tum human-like agent ho jo mushkil ya unclear queries handle karta hai. Tum response draft karte ho jise human staff review karega.
    Tum Inquiry ya Returns Agent se aane wale complex sawalon ke liye use hote ho.
    """
)

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="🏍️ Customer Support Chat", layout="centered")
st.markdown("##  Customer Support Chat")
st.caption("AI-based support assistant for your online store")

# ---------- INPUT FORM ----------
with st.form("support_form"):
    user_query = st.text_input("💬 Ask your question:")
    submitted = st.form_submit_button("Submit")

# ---------- MAIN HANDLER ----------
async def handle_support_query(query):
    faq_answer = search_faq(query)
    if "Maaf" not in faq_answer:
        return faq_answer

    response = await Runner.run(
        starting_agent=inquiry_agent,
        input=[{"role": "user", "content": query}],
        run_config=config,
    )

    match = re.search(r'search_faq\(["\'](.+?)["\']\)', response.final_output)
    if match:
        tool_query = match.group(1)
        return search_faq(tool_query)

    if "escalate_to_returns" in response.final_output:
        policy_answer = search_return_policy(query)
        if "specific information" not in policy_answer:
            return policy_answer
        response = await Runner.run(
            starting_agent=returns_agent,
            input=[{"role": "user", "content": query}],
            run_config=config,
        )

    if "escalate_to_human" in response.final_output:
        response = await Runner.run(
            starting_agent=escalation_agent,
            input=[{"role": "user", "content": query}],
            run_config=config,
        )

    return response.final_output

# ---------- MAIN ----------
if submitted:
    if not user_query.strip():
        st.warning("⚠️ Please enter a valid question.")
    else:
        with st.spinner("🔍 Processing your request..."):
            final_response = asyncio.run(handle_support_query(user_query))
            st.success("✅ Response:")
            st.markdown(final_response)
