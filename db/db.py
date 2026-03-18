from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

CONNECTION_STRING = 'mysql+pymysql://akashnair@localhost:admin@host.docker.internal:3306'

engine = create_engine(CONNECTION_STRING, echo=True)

db_name = 'tasks'
db_status = False

try:
    with engine.connect() as connection:
        connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
        print(f"Database {db_name} created successfully")
        db_status = True
except Exception as e:
    print("Could not initialize database: ", e)

if db_status == True:
    DATABASE_URL = CONNECTION_STRING+f'/{db_name}'
    engine = create_engine(DATABASE_URL, echo=True)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    print('Database created.')
    session.close()
else:
    print('Can\'t create database due to internal error.')