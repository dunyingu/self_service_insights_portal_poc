import streamlit as st
from app.graph import graph
st.set_page_config(page_title="Insights Portal", layout="wide")
st.title("💬 Multi‑Agent NLP Insights Portal (v2)")

if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

with st.sidebar:
    st.write("Session:", st.session_state.session_id)
    email_to = st.text_input("Email results to (optional)", value="")
    send_email = st.checkbox("Send email", value=False)
    st.caption("Demo mode: set USE_FAKE_DB=true to use local sample data.")

user_id = st.text_input("Your user id", value="user@example.com")
question = st.text_input("Ask a question about your data", placeholder="e.g., Daily sales in VIC last 7 days")
ask = st.button("Ask")

if ask and question:
    with st.spinner("Thinking..."):
        out = graph.invoke({
            "user_id": user_id,
            "session_id": st.session_state.session_id,
            "question": question,
            "send_email": send_email,
            "email_to": email_to or None,
        })
    st.subheader("Insights")
    st.write(out.get("insights", ""))
    spec = out.get("chart_spec", {})
    data = out.get("data_json", [])
    if spec:
        st.vega_lite_chart(spec.get("data", {}).get("values", []), spec=spec, use_container_width=True)
    st.subheader("Sample rows")
    st.dataframe(out.get("dataframe_preview", []))
    with st.expander("Raw JSON"):
        st.json(data)
