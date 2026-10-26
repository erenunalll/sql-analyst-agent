import os
import sqlglot
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL
from openai import OpenAI

load_dotenv()

connection_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "3306"),
    database=os.getenv("DB_NAME")
)

engine = create_engine(connection_url)

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("BASE_URL")
)

def get_database_schema():
    inspector = inspect(engine)
    schema = {}

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)

        schema[table_name] = [
            {
            "column" : column["name"],
            "type" : str(column["type"]),
            "nullable" : column["nullable"],
            "primary_key" : column.get("primary_key", False)
            } for column in columns
        ]

    return schema


def validate_sql(sql: str) -> str:
    statements = sqlglot.parse(sql, read="mysql")

    if len(statements) != 1 or statements[0] is None:
        raise ValueError("Only one SQL statement is allowed.")

    query = statements[0]

    if not isinstance(query, sqlglot.exp.Query):
        raise ValueError("Only read queries are allowed.")

    if not isinstance(query, sqlglot.exp.Select):
        raise ValueError("Only SELECT queries are allowed.")

    if query.args.get("into") is not None:
        raise ValueError("SELECT INTO is not allowed.")

    return query.sql(dialect="mysql")
    


def run_query(sql: str):
    sql = validate_sql(sql)

    with engine.connect() as connection:
        result = connection.execute(text(sql))
        rows = [dict(row._mapping) for row in result]

        return rows


def generate_sql(question, schema):
    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[
            {
                "role": "system",
                "content": """
                You are a MySQL SQL query generator.
                Return exactly one SELECT query.
                Use only tables and columns in the given schema.
                Do not include Markdown or explanations.
                """
            },
            {
                "role": "user",
                "content": f"""
                Database schema:
                {schema}

                User question:
                {question}
                """
            }
        ],
        temperature=0
    )

    sql = response.choices[0].message.content.strip()

    return sql


if __name__=="__main__":
    schema = get_database_schema()
    question = """
    Delete the people named Ali.
    """
    sql = generate_sql(question, schema)

    try:
        rows = run_query(sql)
        
        for row in rows:
            print(row)
    except Exception as e:
        print(f"An error occured: {e}")
        print(f"ERROR on SQL statement: {sql}")