# import os
# import psycopg2

# def get_db_connection():
#     if 'ON_HEROKU' in os.environ:
#         connection = psycopg2.connect(
#             os.getenv('DATABASE_URL'),
#             sslmode='require'
#         )
#     else:
#         connection = psycopg2.connect(
#             host='localhost',
#             database=os.getenv('POSTGRES_DATABASE'),
#             user=os.getenv('POSTGRES_USERNAME'),
#             password=os.getenv('POSTGRES_PASSWORD')
#         )
#     return connection
import os
import psycopg2


def get_db_connection():
    # Heroku production database
    if os.getenv("ON_HEROKU") == "true":
        return psycopg2.connect(
            os.getenv("DATABASE_URL"),
            sslmode="require"
        )

    # Local development database
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DATABASE"),
        user=os.getenv("POSTGRES_USERNAME"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )
