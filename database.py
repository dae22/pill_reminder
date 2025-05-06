from databases import Database
from config import DATABASE_URL


database = Database(DATABASE_URL)

async def init_db():
    await database.execute(
        """
        CREATE TABLE IF NOT EXIST users(
            id SERIAL PRIMARY KEY,
            user_id BIGINT UNIQUE NOT NULL
            )
        """
    )
    await database.execute(
        """
        CREATE TABLE IF NOT EXIST pills(
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id),
            name TEXT NOT NULL,
            time TIME NOT NULL
            )
        """
    )
