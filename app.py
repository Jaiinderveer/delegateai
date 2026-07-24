import json
import streamlit as st
from database import save_contacts
from pages.save_tasks import page_tasks
from pages.execute_calls import page_calls
from pages.dashboard import page_dashboard
def main():
    # save_contacts()
    pg = st.navigation([
        st.Page(page_tasks,title='Save Tasks'),
        st.Page(page_calls,title='Execute Calls'),
        st.Page(page_dashboard,title='Dashboard')
    ])
    pg.run()
if __name__ == '__main__':
    main()