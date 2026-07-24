import streamlit as st
import time
from ai_agent import agentic_save

def page_tasks():
    st.set_page_config(page_title='Agentic - Save Tasks')
    st.subheader('Write a Task to Delegate')
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])

    user_input = st.chat_input('Type Your Task here')

    if user_input:

        message = {
            'role': 'user',
            'content': user_input
        }

        st.session_state.messages.append(message)

        with st.chat_message(message['role']):
            st.markdown(message['content'])

        input_list = [
            {"role": "user", "content": user_input}
        ]

        result = agentic_save(input_list=input_list)
        
        message = {
            'role': 'assistant',
            'content': result
        }

        st.session_state.messages.append(message)

        with st.chat_message(message['role']):
            typing_placeholder = st.empty()
            typing_text = ''
            for character in message['content']:
                typing_text += character
                typing_placeholder.markdown(typing_text)
                time.sleep(0.03)

        

    
        