import streamlit as st

st.set_page_config(page_title="Herb-Drug Checker", page_icon="🌿")

st.title("🌿 Herb-Drug Checker (Minimal Test)")
st.write("If you see this, the app is working.")

# Simple counter to detect reloads
if 'count' not in st.session_state:
    st.session_state.count = 0
st.session_state.count += 1
st.write(f"Page reload count: {st.session_state.count}")

st.button("Click me – does it reload?")
