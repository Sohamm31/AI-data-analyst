import pandas as pd
import re
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

def clean_column_name(col_name: str) -> str:
    """Cleans column names to be SQL-friendly."""
    col_name = str(col_name)
    col_name = re.sub(r'[^\w\s]', '', col_name)
    col_name = re.sub(r'\s+', '_', col_name.strip())
    return col_name.lower()

async def process_and_store_file(file: UploadFile, db: Session) -> str:
    """
    Reads a data file and manually controls table creation to ensure robust data types,
    then appends the data. This is the most robust method.
    """
    filename = file.filename
    file_content = file.file

    try:
        # Step 1: Read the file, forcing all columns to string type initially.
        # This prevents pandas from incorrectly guessing data types.
        if filename.endswith('.csv'):
            df = pd.read_csv(file_content, on_bad_lines='skip', dtype=str)
        elif filename.endswith('.tsv'):
            df = pd.read_csv(file_content, sep='\t', on_bad_lines='skip', dtype=str)
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_content, dtype=str)
        elif filename.endswith('.json'):
            df = pd.read_json(file_content, dtype=str)
        elif filename.endswith('.parquet'):
            # Parquet files have their own types; reading as string might not be ideal
            # but is safer for this workflow. For performance, you might omit dtype=str.
            df = pd.read_parquet(file_content)
        elif filename.endswith('.feather'):
            df = pd.read_feather(file_content)
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported file format. Please upload a CSV, TSV, Excel, "
                    "JSON, Parquet, or Feather file."
                )
            )

        # Step 2: Clean column names.
        def clean_column_name(col_name: str, idx: int) -> str:
            col_name = str(col_name).strip()
            col_name = re.sub(r'[^\w\s]', '', col_name)
            col_name = re.sub(r'\s+', '_', col_name)
            col_name = col_name.lower()
            if not col_name:  # if empty after cleaning
                col_name = f"column_{idx+1}"
            return col_name

        df.columns = [clean_column_name(col, idx) for idx, col in enumerate(df.columns)]




        # Step 3: Generate a unique table name.
        base_filename = re.sub(r'\W+', '_', filename.split('.')[0])
        table_name = f"data_{base_filename}_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"

        # --- Manual Table Creation Logic ---

        # Step 4A: Manually construct the CREATE TABLE SQL statement.
        create_table_sql = f"CREATE TABLE `{table_name}` (\n"
        column_definitions = []
        # We convert DataFrame dtypes to SQL types
        for col_name, dtype in df.dtypes.items():
            if 'object' in str(dtype):
                # Use MEDIUMTEXT for all text to be absolutely safe (up to 16MB)
                sql_type = 'MEDIUMTEXT'
            elif 'int' in str(dtype):
                sql_type = 'BIGINT'
            elif 'float' in str(dtype):
                sql_type = 'DOUBLE'
            else:
                sql_type = 'MEDIUMTEXT'  # Default to text for any other types
            column_definitions.append(f"`{col_name}` {sql_type}")
        
        create_table_sql += ",\n".join(column_definitions)
        create_table_sql += "\n);"
        
        try:
            # Step 4B: Execute our manual CREATE TABLE command.
            db.execute(text(create_table_sql))
            db.commit()

            # Step 4C: Use df.to_sql ONLY to append data into the table we just created.
            df.to_sql(
                table_name,
                con=db.get_bind(),
                if_exists='append',  # Use 'append' as the table already exists
                index=False,
                chunksize=1000 
            )
        except Exception as e:
            db.rollback() # Rollback changes if data insertion fails
            raise e
            
        # --- End of Manual Control Logic ---

        return table_name

    except Exception as e:
        print(f"An error occurred in file_handler: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")