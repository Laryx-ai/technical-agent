import streamlit as st

pg = st.navigation([
    st.Page("pages/1_Chat.py",           title="Chat",           icon="💬"),
    st.Page("pages/2_Knowledge_Base.py", title="Knowledge Base", icon="📚"),
    st.Page("pages/3_Agent_Config.py",   title="Settings",       icon="⚙️"),
    st.Page("pages/4_Docs.py",           title="Docs",           icon="📖"),
    st.Page("pages/5_Logs.py",           title="Logs",           icon="📝"),
])
pg.run()
