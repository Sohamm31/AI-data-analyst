import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.db.database import engine
from langchain_openai import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.chains import create_sql_query_chain
from openai import APIError
from sqlalchemy import text

def get_sql_agent_response(db_uri: str, table_name: str, conversation_prompt: str) -> str:
    """
    Gets a natural language response from a database using a multi-step process
    that includes conversation history for context.
    """
    try:
        # STEP 1: Initialize the LLM
        llm = ChatOpenAI(
            model="openai/gpt-oss-20b:free",
            temperature=0,
            openai_api_key=settings.OPENROUTER_KEY,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
              "HTTP-Referer": "http://localhost:8000",
              "X-Title": "AI Data Analyst"
            }
        )

        # STEP 2: Generate and cleanly extract the SQL Query using the full conversation
        db = SQLDatabase.from_uri(db_uri, include_tables=[table_name])
        query_generation_chain = create_sql_query_chain(llm, db)

        general_sql_instruction = (
            "You are a helpful AI data analyst. Based on the conversation history and the user's final question, generate a single, highly compatible SQL query to answer the question.\n"
            "IMPORTANT GUIDELINES FOR SQL GENERATION:\n"
            "1. **Use Highly Compatible SQL:** Adhere to the ANSI SQL (SQL-92) standard.\n"
            "2. **Avoid Modern Functions:** Do not use advanced or vendor-specific functions like JSON_TABLE.\n"
            "3. **Goal:** The query must be runnable on older database systems."
        )

        # We now pass the full conversation history to the AI
        enhanced_prompt = f"{general_sql_instruction}\n\nConversation History:\n{conversation_prompt}"
        
        raw_response = query_generation_chain.invoke({"question": enhanced_prompt})

        print("--- Raw Response from LLM ---")
        print(raw_response)
        print("-----------------------------")

        # Extract the SQL query from the model's structured text output
        if "SQLQuery:" in raw_response:
            sql_query = raw_response.split("SQLQuery:")[-1].strip()
            # More robust cleaning to handle markdown and backticks
            if '```' in sql_query:
                sql_query = sql_query.split('```')[1]
            sql_query = sql_query.replace('sql', '').replace('`', '').strip()
            if "SQLResult:" in sql_query:
                 sql_query = sql_query.split("SQLResult:")[0].strip()
        else:
            sql_query = raw_response.strip()

        if sql_query.endswith(';'):
            sql_query = sql_query[:-1]
        
        if not (sql_query.upper().startswith("SELECT") or sql_query.upper().startswith("WITH")):
            return "The AI generated an invalid response. It did not produce a readable SQL query."
        
        print("--- Cleanly Extracted SQL Query ---")
        print(sql_query)
        print("---------------------------------")
        
        safe_sql_query = sql_query.replace('%', '%%')

    except APIError as e:
        print(f"--- OPENROUTER API ERROR ---\nStatus Code: {e.status_code}\nResponse Body: {e.response.text}\n--------------------------")
        return "There was an error communicating with the AI service. Please check the server logs for details."
    except Exception as e:
        return f"Error during the query generation step: {str(e)}"

    # STEP 3: Execute the REAL query against the database
    try:
        with engine.connect() as connection:
            result_df = pd.read_sql_query(text(safe_sql_query), connection)
            if result_df.empty:
                return "The query ran successfully, but it returned no results."

            # Truncate large results before sending back to the LLM
            if len(result_df) > 30:
                sample_df = result_df.head(30)
                result_str = sample_df.to_string() + f"\n\n... (and {len(result_df) - 30} more rows)"
            else:
                result_str = result_df.to_string()

    except SQLAlchemyError as e:
        return f"Database Error: The generated SQL query failed to run. Details: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred while fetching data: {str(e)}"

    # STEP 4: Convert the REAL data into a natural language answer
    try:
        # Get the last user question from the conversation prompt for context
        last_user_question = conversation_prompt.split("Human:")[-1].strip()

        prompt_for_answer = f"""
        Based on the final user question and the following real data, provide a concise, natural language answer.

        Final User Question:
        "{last_user_question}"

        Real Data from the database:
        "{result_str}"

        Answer:
        """
        final_answer_response = llm.invoke(prompt_for_answer)
        return final_answer_response.content

    except Exception as e:
        return f"Error generating the final answer: {str(e)}"
