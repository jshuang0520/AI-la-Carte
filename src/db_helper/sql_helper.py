import os
import pandas as pd
from sqlalchemy import create_engine
import datetime

def _convert_time_columns(df):
    """
    Convert datetime.time objects to ISO format strings
    """
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, datetime.time) if x is not None else False).any():
            df[col] = df[col].apply(
                lambda x: x.strftime('%H:%M:%S') if isinstance(x, datetime.time) else x
            )
    return df

def excel_to_sql(dir_in_root: str) -> str:
    """
    Convert Excel files in the specified directory to SQLite database tables.

    The directory should be located in the project root directory.

    :param dir_in_root: directory (just name) containing Excel files.
    :return: path to the SQLite database.
    """
    # Configure paths.
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, '')
    db_path = os.path.join(project_root, 'data/cafb.db')
    # Create engine.
    engine = create_engine(f'sqlite:///{db_path}')
    # Process files.
    for filename in os.listdir(data_dir):
        if filename.endswith('.xlsx'):
            file_path = os.path.join(data_dir, filename)
            table_name = os.path.splitext(filename)[0] \
                .replace(' ', '_') \
                .replace('-', '_') \
                .lower()
            try:
                # Read and preprocess data.
                df = pd.read_excel(file_path)
                df = _convert_time_columns(df)
                # Handle date columns explicitly.
                date_cols = df.select_dtypes(include=['datetime64']).columns
                for col in date_cols:
                    df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                # Store in database.
                df.to_sql(
                    name=table_name,
                    con=engine,
                    index=False,
                    if_exists='replace',
                    chunksize=500
                )
                print(f"{filename} → {table_name}")
            except Exception as e:
                print(f"Error with {filename}: {str(e)}")
    return db_path  


