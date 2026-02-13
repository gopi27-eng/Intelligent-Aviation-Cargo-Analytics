import streamlit as st
import os
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# LangChain & Tools
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_ollama import ChatOllama
from langchain_experimental.tools import PythonAstREPLTool

load_dotenv(".env")

# --- PAGE CONFIG ---
st.set_page_config(page_title="AeroLogic AI", page_icon="🧠", layout="wide")
plt.style.use('dark_background')

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.title("⚙️ Controls")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    st.info("Connected to: Supabase Cloud")
    st.info("Model: Gemma 3:4b (Local)")

st.title("🧠 AeroLogic AI: Intelligent Cargo Analytics")

# --- 1. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. DATABASE & AGENT SETUP ---
DB_URI = os.getenv("DATABASE_URL")

@st.cache_resource
def get_agent_executor(uri):
    engine = create_engine(uri, pool_pre_ping=True)
    db = SQLDatabase(engine)
    llm = ChatOllama(model="gemma3:4b", temperature=0, num_ctx=4096)
    python_tool = PythonAstREPLTool()

    system_prefix = """
    You are a Senior Aviation Cargo Analyst. 
    The ONLY table available is named "csv Ai".

    CRITICAL SQL RULES:
    1. Every time you write a query, you MUST wrap the table name in double quotes like this: FROM "csv Ai".
    2. You MUST wrap column names in double quotes too: "Origin", "Vol_wt".
    3. If you do not use double quotes for the table name, the query WILL fail.
    4. "Damage_Rate" is TEXT; use CAST("Damage_Rate" AS FLOAT) for any math.

    Example of the ONLY correct way to query this table:
    SELECT "Origin", SUM("Vol_wt") FROM "csv Ai" GROUP BY "Origin" ORDER BY SUM("Vol_wt") DESC LIMIT 5;
    """
    return create_sql_agent(
        llm=llm, 
        db=db, 
        agent_type="zero-shot-react-description",
        extra_tools=[python_tool],
        prefix=system_prefix,
        verbose=True,
        handle_parsing_errors=True
    )

# --- 3. UI EXECUTION ---
if DB_URI:
    try:
        agent_executor = get_agent_executor(DB_URI)

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "fig" in message:
                    st.pyplot(message["fig"])

        if prompt := st.chat_input("Ask about cargo volume, delays, or safety risks..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("🤖 Analyzing records..."):
                    # We pass 'handle_parsing_errors' to manage the agent's markdown mistakes
                    response = agent_executor.invoke({"input": prompt})
                    answer = response["output"]
                    st.markdown(answer)
                    
                    message_data = {"role": "assistant", "content": answer}
                    
                    # --- IMPROVED PLOT CAPTURE ---
                    fig = plt.gcf()
                    if len(fig.get_axes()) > 0:
                        fig.patch.set_facecolor('#0e1117') 
                        st.pyplot(fig)
                        message_data["fig"] = fig 
                        # Clear for next use to avoid overlapping charts
                        plt.close(fig) 
                    
                    st.session_state.messages.append(message_data)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.warning("DATABASE_URL missing.")