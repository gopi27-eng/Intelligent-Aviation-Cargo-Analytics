import streamlit as st
import os
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_ollama import ChatOllama  # New local dependency
from sqlalchemy import create_engine

# --- PAGE CONFIG ---
st.set_page_config(page_title="SkyQuest: Local AI", page_icon="✈️", layout="wide")

st.title("✈️ SkyQuest: Local Intelligent Cargo Assistant")
st.info("Running locally via Ollama - Unlimited queries, no API limits.")

# --- 1. DATABASE CONNECTION ---
# Your Supabase URL from your .env file
DB_URI = os.getenv("DATABASE_URL")

@st.cache_resource
def get_db_connection(uri):
    # Using pool_pre_ping to keep the cloud connection to Supabase stable
    engine = create_engine(uri, pool_pre_ping=True)
    return SQLDatabase(engine)

if DB_URI:
    try:
        db = get_db_connection(DB_URI)
        
        # --- 2. INITIALIZE LOCAL LLM (OLLAMA) ---
        # Make sure you have run 'ollama pull llama3' in your terminal
        llm = ChatOllama(
            model="llama3", 
            temperature=0
        )

        # Senior Analyst Persona - Crucial for handling your "csv Ai" table
        system_prefix = """
        You are a Senior Aviation Cargo Analyst. 
        The data is in a table named "csv Ai". 
        ALWAYS wrap the table name "csv Ai" and columns with spaces in double quotes in your SQL.
        
        Aviation Context:
        - 'Vol_wt' is Volume Weight.
        - 'Undiclred_DG' is Undeclared Dangerous Goods.
        - 'Total _pices' is the count of items.
        """

        # --- 3. CREATE SQL AGENT ---
        agent_executor = create_sql_agent(
            llm, 
            db=db, 
            agent_type="tool-calling", # Updated for modern local models
            prefix=system_prefix,
            verbose=True
        )

        # --- 4. CHAT UI ---
        user_input = st.text_input("Ask about your shipment data (e.g., 'How many flights went to BOM?'):")

        if user_input:
            with st.spinner("🤖 Local LLM is processing your request..."):
                response = agent_executor.invoke(user_input)
                st.success(response["output"])
                
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
else:
    st.warning("Please ensure DATABASE_URL is set in your .env file.")