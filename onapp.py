import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv(r'C:\Users\Gopi\Desktop\Intelligent Aviation Cargo Analytics\.env')

st.set_page_config(page_title="Cargo Cloud AI", page_icon="☁️")

st.title("✈️ Intelligent Cargo Assistant (Cloud Edition)")
st.info("Ask any question about our 100k+ shipment records in plain English.")

# 1. Database Connection
# Replace with your Supabase/Neon connection string
# Usually starts with: postgresql://postgres...
DB_URI = os.getenv("DATABASE_URL") 

if DB_URI:
    try:
        db = SQLDatabase.from_uri(DB_URI)
        
        # 2. Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0
        )

        # 3. Create the SQL Agent
        agent_executor = create_sql_agent(
            llm, 
            db=db, 
            agent_type="openai-tools", # Best for structured reasoning
            verbose=True
        )

        # 4. Chat UI
        user_input = st.text_input("Example: Which month had the most delays?")

        if user_input:
            with st.spinner("🤖 Consulting the database..."):
                # The agent generates and runs the SQL automatically
                response = agent_executor.invoke(user_input)
                st.success(response["output"])
                
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
else:
    st.warning("Database URL not found. Please set your environment variables.")