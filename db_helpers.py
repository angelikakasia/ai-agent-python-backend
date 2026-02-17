import os
import psycopg2


def get_db_connection():
    database_url = os.getenv("DATABASE_URL")

    # Production (Heroku or any cloud)
    if database_url:
        return psycopg2.connect(
            database_url,
            sslmode="require"
        )

    # Local development
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DATABASE"),
        user=os.getenv("POSTGRES_USERNAME"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )

