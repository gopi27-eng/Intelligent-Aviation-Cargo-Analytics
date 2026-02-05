import streamlit as st
import os
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_ollama import ChatOllama
from sqlalchemy import create_engine

# --- PAGE CONFIG ---
st.set_page_config(page_title="SkyQuest: Gemma 3 Edition", page_icon="✈️", layout="wide")

st.title("✈️ SkyQuest: Intelligent Cargo Assistant")
st.info("Powered by Gemma 3:4b (Local) & Supabase (Cloud)")

# --- 1. DATABASE CONNECTION ---
DB_URI = os.getenv("DATABASE_URL")

@st.cache_resource
def get_db_connection(uri):
    # pool_pre_ping keeps your connection to Supabase active
    engine = create_engine(uri, pool_pre_ping=True)
    return SQLDatabase(engine)

if DB_URI:
    try:
        db = get_db_connection(DB_URI)
        
        # --- 2. INITIALIZE GEMMA 3:4B ---
        # Gemma 3 is excellent at following structured system prompts
        llm = ChatOllama(
            model="gemma3:4b", 
            temperature=0
        )

        # Senior Analyst Persona
        system_prefix = """
        You are a Senior Aviation Cargo Analyst. 
        The shipment data is in a table named "csv Ai". 
        
        CRITICAL RULES:
        1. Always wrap the table name "csv Ai" in double quotes.
        2. Column mapping: 'Vol_wt' = Volume Weight, 'Undiclred_DG' = Dangerous Goods.
        3. Spelling: The database uses "Total _pices" (with a space and an 'i').
        """

        # --- 3. CREATE AGENT ---
        agent_executor = create_sql_agent(
            llm, 
            db=db, 
            agent_type="tool-calling", # Gemma 3 supports native function calling
            prefix=system_prefix,
            verbose=True
        )

        # --- 4. CHAT UI ---
        user_input = st.text_input("Analyze your 82k records:")

        if user_input:
            with st.spinner("🤖 Gemma 3 is querying the database..."):
                response = agent_executor.invoke(user_input)
                st.success(response["output"])
                
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
else:
    st.warning("Database URL not found. Ensure your .env file is updated.")