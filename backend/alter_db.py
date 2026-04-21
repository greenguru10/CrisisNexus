from database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE needs ALTER COLUMN category TYPE varchar(255);'))
    conn.commit()
    print('Success')
