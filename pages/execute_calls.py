import streamlit as st
from caller_agent import execute_pending_calls, get_conversation_transcript
from database import tasks_collection

# Function to execute calls
def page_calls():
    st.title("Execute Calls")

    # ------------------ Task Board ------------------
    st.subheader("Task Board")

    for task in tasks_collection.find():
        st.write(
            f"{task['title']} - {task['status']} - {task['action']} - {task['contact_name']}"
        )

    st.divider()

    if st.button("Start Pending Calls"):
        result = execute_pending_calls()

        for line in result:
            st.success(line)

    # ------------------ Completed Calls ------------------
    st.divider()
    st.subheader("Completed Call Transcripts")

    completed = list(tasks_collection.find({"status": "COMPLETED"}))

    if not completed:
        st.info("No completed calls yet.")
        return

    for task in completed:

        with st.expander(
            f"{task['title']} • {task['contact_name']}",
            expanded=False,
        ):

            st.write(f"**Task:** {task['description']}")
            st.write(f"**Called:** {task['contact_name']}")
            st.write(f"**Status:** {task['status']}")

            st.divider()

            try:
                conversation = get_conversation_transcript(
                    task["conversation_id"]
                )
                
                for message in conversation.transcript:

                    role = (
                        "assistant"
                        if message.role == "agent"
                        else "user"
                    )

                    with st.chat_message(role):
                        st.write(message.message)

            except Exception as e:
                st.error(f"Could not load transcript.\n\n{e}")