import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.db.database import engine
from langchain_openai import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.chains import create_sql_query_chain
from openai import APIError
from sqlalchemy import text
import json

def get_sql_agent_response(db_uri: str, table_name: str, conversation_prompt: str) -> dict:
    """
    Gets a response from the database, handling both text and chart requests.
    Always returns a dictionary containing the answer, the generated SQL query,
    and a preview of the data to ensure transparency.
    """
    sql_query = ""
    result_df = pd.DataFrame()
    
    try:
        # STEP 1: Initialize LLM
        llm = ChatOpenAI(
            model="openai/gpt-oss-20b:free",
            temperature=0,
            openai_api_key=settings.OPENROUTER_KEY,
            base_url="https://openrouter.ai/api/v1",
            default_headers={"HTTP-Referer": "http://localhost:8000", "X-Title": "AI Data Analyst"}
        )

        # STEP 2: Generate and extract SQL query
        db = SQLDatabase.from_uri(db_uri, include_tables=[table_name])
        query_generation_chain = create_sql_query_chain(llm, db)
        
        general_sql_instruction = (
            "You are a helpful AI data analyst. Based on the conversation history and the user's final question, generate a single, highly compatible SQL query to answer the question.\n"
            "IMPORTANT GUIDELINES FOR SQL GENERATION:\n"
            "1. **Use Highly Compatible SQL:** Adhere to the ANSI SQL (SQL-92) standard.\n"
            "2. **Avoid Modern Functions:** Do not use advanced or vendor-specific functions like JSON_TABLE.\n"
            "3. **Goal:** The query must be runnable on older database systems."
        )
        enhanced_prompt = f"{general_sql_instruction}\n\nConversation History:\n{conversation_prompt}"
        raw_response = query_generation_chain.invoke({"question": enhanced_prompt})

        print("--- Raw Response from LLM ---")
        print(raw_response)
        print("-----------------------------")

        if "SQLQuery:" in raw_response:
            sql_query = raw_response.split("SQLQuery:")[-1].strip()
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
            return {
                "answer": "The AI generated an invalid response. It did not produce a readable SQL query.",
                "sql_query": sql_query,
                "data_preview": None
            }

    except Exception as e:
        return {"answer": f"Error during query generation: {str(e)}", "sql_query": "", "data_preview": None}

    # STEP 3: Execute query
    try:
        safe_sql_query = sql_query.replace('%', '%%')
        with engine.connect() as connection:
            result_df = pd.read_sql_query(text(safe_sql_query), connection)
    except SQLAlchemyError as e:
        return {"answer": f"Database Error: {str(e)}", "sql_query": sql_query, "data_preview": None}
    except Exception as e:
        return {"answer": f"An unexpected error occurred while fetching data: {str(e)}", "sql_query": sql_query, "data_preview": None}


    # STEP 4: Generate final answer and package the results
    try:
        last_user_question = conversation_prompt.split("Human:")[-1].strip()
        
        # Create a preview of the dataframe (top 10 rows) for the response
        preview_df = result_df.head(10)
        data_preview_json = json.loads(preview_df.to_json(orient='split')) if not preview_df.empty else None

        # Truncate the full dataframe for the LLM prompt to keep it concise
        result_str = preview_df.to_string()
        if len(result_df) > 10:
            result_str += f"\n\n... (and {len(result_df) - 10} more rows)"

        chart_keywords = ['chart', 'plot', 'graph', 'visualize', 'diagram', 'bar', 'pie', 'line']
        is_chart_request = any(keyword in last_user_question.lower() for keyword in chart_keywords)

        final_answer = ""

        if is_chart_request and len(result_df.columns) >= 2:
            prompt_for_chart_json = f"""
            Based on the user's question and the following data, you MUST respond with ONLY a valid JSON object that can be used to create a chart with Chart.js.
            The JSON object must have this exact structure: {{"type": "chart", "chart_type": "bar", "data": {{"labels": [], "datasets": [{{"label": "Description", "data": []}}]}}, "title": "Chart Title"}}
            - 'chart_type' can be 'bar', 'line', or 'pie'.
            - 'labels' should be the first column of the data.
            - 'data' should be the second column.
            User's Question: "{last_user_question}"
            Data: {result_df.to_json(orient='split')}
            Valid JSON Response:
            """
            final_response = llm.invoke(prompt_for_chart_json)
            final_answer = final_response.content.strip().replace("```json", "").replace("```", "").strip()
        else:
            prompt_for_answer = f"""
            Based on the final user question and the following real data, provide a concise, natural language answer.
            Final User Question: "{last_user_question}"
            Real Data from the database: "{result_str}"
            Answer:
            """
            final_answer_response = llm.invoke(prompt_for_answer)
            final_answer = final_answer_response.content

        return {
            "answer": final_answer,
            "sql_query": sql_query,
            "data_preview": data_preview_json
        }

    except Exception as e:
        return {"answer": f"Error generating final answer: {str(e)}", "sql_query": sql_query, "data_preview": data_preview_json}
