from databases import Database
from config import DATABASE_URL


database = Database(DATABASE_URL)

async def init_db():
    await database.execute(
        """
        CREATE TABLE IF NOT EXISTS pills(
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            name TEXT NOT NULL,
            time TIME NOT NULL,
            last_taken DATE,
            last_notified TIMESTAMP
            )
        """
    )
