"""
Streamlit UI for Lenny-RAG.

Usage:
  streamlit run app.py
"""

import streamlit as st
from rag import ask

st.set_page_config(page_title="Lenny RAG", layout="centered")

st.title("Lenny's Podcast — Ask Anything")
st.caption("Answers are grounded in ~300 podcast transcripts. Every claim is cited.")

QUESTION_PREVIEW_LIMIT = 150

# Session state initialisation
for key, default in [("input_key", 0), ("last_question", ""), ("answer", ""), ("chunks", [])]:
    if key not in st.session_state:
        st.session_state[key] = default

question = st.text_input(
    label="question",
    placeholder="Ask a question about product strategy...",
    label_visibility="collapsed",
    key=f"question_input_{st.session_state.input_key}",
)

if st.button("Ask", type="primary") and question.strip():
    q = question.strip()
    with st.spinner("Thinking..."):
        answer, chunks = ask(q)
    st.session_state.last_question = q
    st.session_state.answer = answer
    st.session_state.chunks = chunks
    st.session_state.input_key += 1  # incrementing the key forces Streamlit to render a fresh, empty input
    st.rerun()

if st.session_state.last_question:
    q = st.session_state.last_question
    if len(q) > QUESTION_PREVIEW_LIMIT:
        st.markdown(f"**Q: {q[:QUESTION_PREVIEW_LIMIT]}...**")
        with st.expander("View full question"):
            st.write(q)
    else:
        st.markdown(f"**Q: {q}**")

    st.markdown(st.session_state.answer)

    with st.expander("Sources", expanded=False):
        for i, c in enumerate(st.session_state.chunks, 1):
            st.markdown(f"**[{i}] {c['episode']}**")
            st.caption(c["text"])
            if i < len(st.session_state.chunks):
                st.divider()
