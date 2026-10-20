
import csv
import os
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from google import genai

st.set_page_config(
    page_title="Eco-Sort Assistant",
    page_icon="🌍",
    layout="centered",
)

st.title("🌍 Eco-Sort Assistant")
st.subheader("AI-assisted waste sorting research prototype")

st.write(
    "Explore how an AI model classifies waste items and explains "
    "possible disposal methods."
)

st.warning(
    "Guidance may be incorrect. Recycling rules vary by location. "
    "Verify local instructions, especially for hazardous waste."
)

item = st.text_input(
    "Enter a waste item",
    placeholder="e.g. plastic bottle, pizza box, used battery",
    max_chars=200,
)

research_consent = st.checkbox(
    "I agree to save this test item and its AI response locally "
    "for research evaluation. Do not enter personal information."
)

def analyze_item(item_name: str) -> str:
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:
        raise RuntimeError("API key is not configured.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an assistant for cautious waste-sorting guidance.

Analyze this item: {item_name!r}

Use these sections:
1. Likely material category
2. Recycling status: commonly recyclable, commonly not recyclable,
   special handling, or insufficient information
3. Suggested disposal steps
4. Safety precautions
5. Uncertainty and local-rule considerations

Do not claim an item is recyclable everywhere.
Do not invent statistics or local regulations.
If the description is ambiguous, say what extra information is needed.
For batteries, electronics, chemicals, and medical waste, recommend
checking appropriate local collection or disposal guidance.
Keep the response concise.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    if not response.text or not response.text.strip():
        raise ValueError("Empty model response.")

    return response.text.strip()


def save_research_record(item_name: str, answer: str) -> None:
    path = Path("research_results.csv")
    file_exists = path.exists()

    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(
                ["timestamp_utc", "item", "model", "response"]
            )

        writer.writerow(
            [
                datetime.now(timezone.utc).isoformat(),
                item_name,
                "gemini-2.5-flash",
                answer,
            ]
        )


if st.button("Analyze item", type="primary", use_container_width=True):
    if not item.strip():
        st.warning("Enter an item first.")
    else:
        try:
            with st.spinner("Analyzing the item..."):
                answer = analyze_item(item.strip())

            st.markdown("### AI result")
            st.markdown(answer)

            if research_consent:
                save_research_record(item.strip(), answer)
                st.success(
                    "Research record saved locally. "
                    "Review it before using it in an evaluation."
                )
            else:
                st.info(
                    "No research record was saved. "
                    "You can still review the result above."
                )

        except RuntimeError as error:
            if "API key" in str(error):
                st.error(
                    "Configure GEMINI_API_KEY in the secure settings."
                )
            else:
                st.error("The model could not be configured.")
        except Exception:
            st.error(
                "The request failed. Check the API key, model access, "
                "internet connection, and service availability."
            )

st.divider()
st.caption(
    "Research prototype only. AI responses are not verified "
    "official waste-management instructions."
)
