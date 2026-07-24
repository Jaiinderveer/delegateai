import streamlit as st
from caller_agent import fetch_conversation_status
def page_dashboard():
    st.title('Dashboard')
    if st.button('Fetch Conversation Status'):
        result = fetch_conversation_status()
        for line in result:
            st.write(line)