import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

connection_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME")
)

engine = create_engine(connection_url)

with engine.connect() as connection:
    tables = connection.execute(text("SHOW TABLES")).fetchall()
    print("MySQL bağlantısı başarılı!")
    print("Tablolar:", tables)

    employees = connection.execute(
        text("SELECT * FROM employees")
    ).fetchall()

    for employee in employees:
        print(employee)
