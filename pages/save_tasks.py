import time
import streamlit as st
from ai_agent import agentic_save

def page_tasks():
    # Sticky Top Bar
    st.html("""
        <div class="top-bar">
            <div>
                <h3 style="margin: 0; font-size: 17px; color: #F0F6FC;">Agentic Workspace</h3>
                <p style="margin: 2px 0 0 0; font-size: 12px; color: #8B949E;">Delegate natural language tasks directly to AI agents.</p>
            </div>
            <div class="status-badge">
                <div class="status-dot"></div>
                Agent Ready
            </div>
        </div>
    """)

    # Chat Session State (init early so both columns can read it)
    if 'task_messages' not in st.session_state:
        st.session_state.task_messages = []

    main_col, side_col = st.columns([2.6, 1], gap="medium")

    preset_query = None

    with main_col:
        # Quick Suggestion Chips — identical trigger strings to the original
        st.markdown("<p class='section-label'>Quick Presets</p>", unsafe_allow_html=True)
        chip_col1, chip_col2, chip_col3 = st.columns(3)
        with chip_col1:
            if st.button("📅 Schedule a Meeting with Jai", use_container_width=True):
                preset_query = "call jai regarding the meeting tomorrow at 6 PM."
        with chip_col2:
            if st.button("📞 Call Contact regarding Update", use_container_width=True):
                preset_query = "Call John regarding the project delivery status."
        with chip_col3:
            if st.button("📊 Query Pending Tasks", use_container_width=True):
                preset_query = "Show me all pending call tasks."

        st.divider()

        # Display Existing Thread
        if not st.session_state.task_messages:
            st.html("""
                <div style="text-align:center; padding: 40px 24px; color: #8B949E;">
                    <div style="font-size: 26px; margin-bottom: 10px;">⚡</div>
                    <div style="font-weight:600; color:#F0F6FC; margin-bottom:4px;">Delegate your first task</div>
                    <div style="font-size: 13px;">Try a quick preset above, or type a request below — e.g. "Call Jai regarding the Monte Carlo submission."</div>
                </div>
            """)
        for message in st.session_state.task_messages:
            with st.chat_message(message['role']):
                st.markdown(message['content'])

        # Handle Input (User Typed or Preset Clicked)
        user_input = st.chat_input('Write a task to delegate (e.g., "Call Jai regarding Monte Carlo submission")...')

        active_prompt = user_input or preset_query

        if active_prompt:
            # Append User Message
            user_msg = {'role': 'user', 'content': active_prompt}
            st.session_state.task_messages.append(user_msg)

            if not user_input:  # If clicked preset, manually render user bubble
                with st.chat_message('user'):
                    st.markdown(active_prompt)

            # Call Backend AI Agent
            input_list = [{"role": "user", "content": active_prompt}]
            response_text = agentic_save(input_list=input_list)

            # Append Assistant Message
            assistant_msg = {'role': 'assistant', 'content': response_text}
            st.session_state.task_messages.append(assistant_msg)

            # Typing Effect Output
            with st.chat_message('assistant'):
                typing_placeholder = st.empty()
                running_text = ""
                for char in response_text:
                    running_text += char
                    typing_placeholder.markdown(running_text)
                    time.sleep(0.004)

    with side_col:
        st.markdown("<p class='section-label'>Recent Activity</p>", unsafe_allow_html=True)
        recent_user_msgs = [m['content'] for m in st.session_state.task_messages if m['role'] == 'user'][-4:][::-1]

        if recent_user_msgs:
            rows = "".join(
                f"""<div class="stat-row">
                        <span class="stat-row-label" style="max-width: 100%; white-space: normal;">{msg[:70]}{'…' if len(msg) > 70 else ''}</span>
                    </div>"""
                for msg in recent_user_msgs
            )
            st.html(f'<div class="glass-card glass-card-tight">{rows}</div>')
        else:
            st.html("""
                <div class="glass-card glass-card-tight" style="color:#8B949E; font-size: 13px;">
                    Nothing delegated yet this session.
                </div>
            """)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("<p class='section-label'>Tips</p>", unsafe_allow_html=True)
        st.html("""
            <div class="glass-card glass-card-tight" style="font-size: 12.5px; line-height: 1.7; color: #C9D1D9;">
                <span class="pill pill-accent">⚡ Action</span> "Call &lt;contact&gt; regarding &lt;topic&gt;"<br><br>
                <span class="pill pill-neutral">🔍 Query</span> "Show pending / failed calls"<br><br>
                <span class="pill pill-neutral">🎙️ Voice</span> Use the mic icon in the composer to dictate.
            </div>
        """)