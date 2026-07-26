import os
import logging
import streamlit as st
from database import get_calls_query
from elevenlabs.client import ElevenLabs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_transcript_from_api(conversation_id):
    """
    Calls ElevenLabs API dynamically, parses transcript object, and formats for Streamlit.
    """
    if not conversation_id:
        return [{"role": "assistant", "content": "*System Note: No ElevenLabs conversation ID logged for this task.*"}]

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return [{"role": "assistant", "content": "⚠️ **Config Error:** `ELEVENLABS_API_KEY` missing from environment variables."}]

    try:
        client = ElevenLabs(api_key=api_key)
        response = client.conversational_ai.conversations.get(conversation_id=conversation_id)
        
        # Dynamic object parsing
        if hasattr(response, "model_dump"):
            conv_data = response.model_dump()
        elif hasattr(response, "dict"):
            conv_data = response.dict()
        elif isinstance(response, dict):
            conv_data = response
        else:
            conv_data = vars(response)
            
        transcript_data = conv_data.get("transcript", [])
        
        if not transcript_data:
            return [{"role": "assistant", "content": "*System Note: ElevenLabs conversation transcript is currently empty.*"}]

        formatted_transcript = []
        for msg in transcript_data:
            if isinstance(msg, dict):
                raw_role = msg.get("role", "user").lower()
                content = msg.get("message", msg.get("text", "[No Content]"))
            else:
                raw_role = getattr(msg, "role", "user").lower()
                content = getattr(msg, "message", getattr(msg, "text", "[No Content]"))
                
            streamlit_role = "assistant" if raw_role in ["agent", "assistant", "system"] else "user"
            formatted_transcript.append({"role": streamlit_role, "content": content})
            
        return formatted_transcript

    except Exception as e:
        error_str = str(e)
        logger.error(f"Transcript Fetch Failed: {error_str}")
        return [{"role": "assistant", "content": f"⚠️ **API Error:** Unable to retrieve transcript. (`{error_str}`)"}]


def _status_pill(status_text: str) -> str:
    """Presentation-only helper: maps a status string to a styled pill. No business logic."""
    s = (status_text or "").upper()
    if s in ("COMPLETED",):
        return f'<span class="pill pill-success">● {s}</span>'
    if s in ("FAILED",):
        return f'<span class="pill pill-danger">● {s}</span>'
    if s in ("PENDING", "CALLING"):
        return f'<span class="pill pill-warning">● {s}</span>'
    return f'<span class="pill pill-neutral">● {s or "UNKNOWN"}</span>'


def page_calls():
    # Sticky Top Bar
    st.html("""
        <div class="top-bar">
            <div>
                <h3 style="margin: 0; font-size: 17px; color: #F0F6FC;">Live Call Monitor</h3>
                <p style="margin: 2px 0 0 0; font-size: 12px; color: #8B949E;">Real-time call queue status and telephony transcript records.</p>
            </div>
            <div class="status-badge" style="border-color: rgba(59, 130, 246, 0.4); color: #60A5FA;">
                <div class="status-dot" style="background-color: #3B82F6; box-shadow: 0 0 8px rgba(59, 130, 246, 0.5);"></div>
                Daemon Active
            </div>
        </div>
    """)

    # Fetch data once; both the stat strip and the panels below read from these
    pending_list = get_calls_query(intent_status="PENDING")
    completed_list = get_calls_query(intent_status="COMPLETED")

    # Operations stat strip (purely computed from the results above — no new queries)
    stat1, stat2, stat3 = st.columns(3)
    with stat1: st.metric("Queue Depth", len(pending_list))
    with stat2: st.metric("Completed Calls", len(completed_list))
    with stat3: st.metric("Monitoring", "Live", delta=None)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.6], gap="medium")

    # Left Column: Queue Status
    with col1:
        st.markdown("<p class='section-label'>Pending Execution Queue</p>", unsafe_allow_html=True)

        if pending_list:
            for task in pending_list:
                with st.container(border=True):
                    st.html(f"""
                        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">
                            <div>
                                <div style="font-weight:600; color:#F0F6FC; font-size:14px;">{task.get('title', 'Untitled Call')}</div>
                                <div style="font-size:12px; color:#8B949E; margin-top:2px;">Contact: {task.get('contact_name', 'Unknown')}</div>
                            </div>
                            {_status_pill(task.get('status', 'PENDING'))}
                        </div>
                    """)
        else:
            st.info("Queue clear. No pending calls waiting.", icon="✨")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("<p class='section-label'>Control Center</p>", unsafe_allow_html=True)
        if st.button("🔄 Refresh Queue & Monitor", use_container_width=True):
            st.rerun()

    # Right Column: Completed Timeline & Transcripts
    with col2:
        st.markdown("<p class='section-label'>Call History & Transcripts</p>", unsafe_allow_html=True)

        if completed_list:
            for task in completed_list:
                contact = task.get('contact_name', 'Unknown')
                title = task.get('title', 'Call')
                created_dt = task.get('created_at')
                date_str = created_dt.strftime("%Y-%m-%d %H:%M") if created_dt else "N/A"
                
                with st.expander(f"📞 {title} — {contact}", expanded=False):
                    st.html(f"""
                        <div style="display:flex; align-items:center; gap:10px; margin-bottom:14px;">
                            {_status_pill('COMPLETED')}
                            <span style="font-size:12px; color:#8B949E;">Logged {date_str}</span>
                        </div>
                    """)

                    # Task Instructions
                    description = task.get('description', 'No description logged.')
                    st.markdown("<p style='font-size: 11px; color: #8B949E; margin-bottom: 6px; text-transform: uppercase; font-weight: 600;'>Task Instructions</p>", unsafe_allow_html=True)
                    st.html(f"""
                        <div style="background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 12px 14px; margin-bottom: 16px; color: #C9D1D9; font-size: 13px;">{description}</div>
                    """)
                    
                    # ElevenLabs Agentic Transcript
                    conversation_id = task.get('conversation_id')
                    if conversation_id:
                        st.markdown("<p style='font-size: 11px; color: #8B949E; margin-bottom: 10px; text-transform: uppercase; font-weight: 600;'>ElevenLabs Call Transcript</p>", unsafe_allow_html=True)
                        
                        transcript_data = fetch_transcript_from_api(conversation_id)
                        with st.container(border=True):
                            for msg in transcript_data:
                                with st.chat_message(msg.get('role', 'user')):
                                    st.write(msg.get('content', ''))
                    else:
                        st.caption("No ElevenLabs `conversation_id` recorded for this call.")
        else:
            st.info("No completed calls found in database history.", icon="📭")