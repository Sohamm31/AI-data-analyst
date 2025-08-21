import pandas as pd
import re
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

def clean_column_name(col_name: str) -> str:
    col_name = str(col_name)
    col_name = re.sub(r'[^\w\s]', '', col_name)
    col_name = re.sub(r'\s+', '_', col_name.strip())
    return col_name.lower()

async def process_and_store_file(file: UploadFile, db: Session) -> str:

    filename = file.filename
    file_content = file.file

    try:

        if filename.endswith('.csv'):
            df = pd.read_csv(file_content, on_bad_lines='skip', dtype=str)
        elif filename.endswith('.tsv'):
            df = pd.read_csv(file_content, sep='\t', on_bad_lines='skip', dtype=str)
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_content, dtype=str)
        elif filename.endswith('.json'):
            df = pd.read_json(file_content, dtype=str)
        elif filename.endswith('.parquet'):

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

        def clean_column_name(col_name: str, idx: int) -> str:
            col_name = str(col_name).strip()
            col_name = re.sub(r'[^\w\s]', '', col_name)
            col_name = re.sub(r'\s+', '_', col_name)
            col_name = col_name.lower()
            if not col_name:  
                col_name = f"column_{idx+1}"
            return col_name

        df.columns = [clean_column_name(col, idx) for idx, col in enumerate(df.columns)]




        base_filename = re.sub(r'\W+', '_', filename.split('.')[0])
        table_name = f"data_{base_filename}_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"


        create_table_sql = f"CREATE TABLE `{table_name}` (\n"
        column_definitions = []
        for col_name, dtype in df.dtypes.items():
            if 'object' in str(dtype):
                sql_type = 'MEDIUMTEXT'
            elif 'int' in str(dtype):
                sql_type = 'BIGINT'
            elif 'float' in str(dtype):
                sql_type = 'DOUBLE'
            else:
                sql_type = 'MEDIUMTEXT' 
            column_definitions.append(f"`{col_name}` {sql_type}")
        
        create_table_sql += ",\n".join(column_definitions)
        create_table_sql += "\n);"
        
        try:
            db.execute(text(create_table_sql))
            db.commit()

            df.to_sql(
                table_name,
                con=db.get_bind(),
                if_exists='append', 
                index=False,
                chunksize=1000 
            )
        except Exception as e:
            db.rollback()
            raise e
            
       

        return table_name

    except Exception as e:
        print(f"An error occurred in file_handler: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")