import time
import streamlit as st
import pandas as pd
from database import get_dashboard_metrics
from ai_agent import agentic_save

def page_dashboard():
    # Sticky Top Bar
    st.html("""
        <div class="top-bar">
            <div>
                <h3 style="margin: 0; font-size: 17px; color: #F0F6FC;">Executive Analytics</h3>
                <p style="margin: 2px 0 0 0; font-size: 12px; color: #8B949E;">Real-time system operational metrics and call performance data.</p>
            </div>
            <div class="status-badge">
                <div class="status-dot"></div>
                Live Database Sync
            </div>
        </div>
    """)
    
    metrics = get_dashboard_metrics()

    # KPI Grid
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1: st.metric("Total Calls", metrics['Total_Calls_All_Time'])
    with kpi2: st.metric("Completed", metrics['Completed_Calls_All_Time'])
    with kpi3: st.metric("Failed", metrics['Failed_Calls_All_Time'])
    with kpi4: st.metric("Pending Queue", metrics['Pending_Calls_Current'])

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Dark Chart & Network Health
    c_col1, c_col2 = st.columns([2, 1])
    
    with c_col1:
        st.markdown("<p class='section-label'>Call Distribution Outcomes</p>", unsafe_allow_html=True)
        chart_df = pd.DataFrame({
            'Outcome': ['Completed', 'Failed', 'Pending'],
            'Volume': [metrics['Completed_Calls_All_Time'], metrics['Failed_Calls_All_Time'], metrics['Pending_Calls_Current']]
        })
        st.bar_chart(chart_df.set_index('Outcome'), color="#3B82F6", height=240)

    with c_col2:
        st.markdown("<p class='section-label'>Telephony Network Health</p>", unsafe_allow_html=True)
        st.metric("Total Retries", metrics['Total_Retries_All_Time'])
        st.metric("Retries Today", metrics['Retries_Today'])
        st.metric("Total Contacts Saved", metrics['Total_Contacts'])

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Insights Panel — surfaces fields already returned by get_dashboard_metrics()
    # that the previous layout computed but never displayed.
    st.markdown("<p class='section-label'>Insights</p>", unsafe_allow_html=True)
    insight_col1, insight_col2 = st.columns(2)

    with insight_col1:
        rows = f"""
            <div class="stat-row">
                <span class="stat-row-label">Total tasks logged (all-time)</span>
                <span class="stat-row-value">{metrics['Total_Tasks_All_Time']}</span>
            </div>
            <div class="stat-row">
                <span class="stat-row-label">Completed today</span>
                <span class="stat-row-value">{metrics['Todays_Completed_Tasks_Count']}</span>
            </div>
            <div class="stat-row">
                <span class="stat-row-label">Most called contact</span>
                <span class="stat-row-value">{metrics['Most_Called_Contact_All_Time']}</span>
            </div>
            <div class="stat-row">
                <span class="stat-row-label">Highest success-rate contact</span>
                <span class="stat-row-value">{metrics['Contact_With_Highest_Success_Rate']}</span>
            </div>
        """
        st.html(f'<div class="glass-card">{rows}</div>')

    with insight_col2:
        unassigned = metrics['Contacts_With_No_Tasks_Assigned']
        unassigned_display = ", ".join(unassigned) if unassigned else "None"
        rows = f"""
            <div class="stat-row">
                <span class="stat-row-label">Calls to deleted contacts</span>
                <span class="stat-row-value">{metrics['Number_Of_Calls_To_Deleted_Contacts']}</span>
            </div>
            <div class="stat-row">
                <span class="stat-row-label">Contacts with no tasks assigned</span>
                <span class="stat-row-value" style="text-align:right; max-width:60%;">{unassigned_display}</span>
            </div>
        """
        st.html(f'<div class="glass-card">{rows}</div>')

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.divider()

    # Conversational Data Analyst Agent
    st.markdown("<h4 style='font-size: 16px; color: #F0F6FC;'>Data Analyst Agent</h4>", unsafe_allow_html=True)
    st.caption("Ask natural language questions regarding database history or system health.")

    if 'dashboard_messages' not in st.session_state:
        st.session_state.dashboard_messages = []

    for msg in st.session_state.dashboard_messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    analyst_input = st.chat_input('e.g., "Why did the last call fail?" or "Summarize overall success rate"')

    if analyst_input:
        st.session_state.dashboard_messages.append({'role': 'user', 'content': analyst_input})
        with st.chat_message('user'):
            st.markdown(analyst_input)

        input_list = [{"role": "user", "content": analyst_input}]
        agent_response = agentic_save(input_list=input_list)

        st.session_state.dashboard_messages.append({'role': 'assistant', 'content': agent_response})

        with st.chat_message('assistant'):
            placeholder = st.empty()
            text_acc = ""
            for char in agent_response:
                text_acc += char
                placeholder.markdown(text_acc)
                time.sleep(0.004)