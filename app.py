from flask import Flask, jsonify, request, g
from dotenv import load_dotenv
import psycopg2, psycopg2.extras
import jwt
import bcrypt
import os
from db_helpers import get_db_connection
from flask_cors import CORS
from auth_middleware import token_required
from agents import agents_blueprint



load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
@app.route("/<path:path>", methods=["OPTIONS"])
def options_handler(path):
    return "", 200

app.register_blueprint(agents_blueprint)



@app.route("/")
def index():
    return "Hello, Brother, Hello, Sister - yes I am working!"


# Encoding JWT token with secret-based signature
@app.route("/sign-token", methods=["GET"])
def sign_token():
    user = {"id": 1, "username": "test", "password": "test"}

    token = jwt.encode(user, os.getenv("JWT_SECRET"), algorithm="HS256")

    return jsonify({"token": token})


# Decoding token to verify JWT signature
@app.route("/verify-token", methods=["POST"])
def verify_token():
    try:
        token = request.headers.get("Authorization").split(" ")[1]
        decoded_token = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        return jsonify({"user": decoded_token})

    except Exception as err:
        return jsonify({"err": err.message})


# # POST /auth/sign-in
@app.route("/auth/sign-up", methods=["POST"])
def sign_up():
    try:
        new_user_data = request.get_json()

        # Establish the connection with the db
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Through the connection, run a SQL command to find existing user in the db
        cursor.execute(
            "SELECT * FROM users WHERE email = %s;", 
            (new_user_data["email"],)
            )

        # Then fetch the user
        existing_user = cursor.fetchone()
        # Close the connection if there is a user and return message specifying existing user
        if existing_user:
            cursor.close()
            return jsonify({"err": "Email already taken"}), 400
        # Hash the password
        hashed_password = bcrypt.hashpw(
            bytes(new_user_data["password"], "utf-8"), bcrypt.gensalt()
        )
        # With no existing user, we can add the user to db and return the user object
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id, email",
            (new_user_data["email"], hashed_password.decode("utf-8")),
        )
        # Grab the user object from db, then commit (save to db) then close connection with the DB
        created_user = cursor.fetchone()
        connection.commit()
        connection.close()

        # Construct the payload
        payload = {"email": created_user["email"], "id": created_user["id"]}
        # Create the token, attaching the payload
        token = jwt.encode({"payload": payload}, os.getenv("JWT_SECRET"))
        # Send the token instead of the user
        return jsonify({"token": token}), 201
    except Exception as err:
        return jsonify({"err": str(err)}), 401


#POST AUTH/SIGN-IN
@app.route("/auth/sign-in", methods=["POST"])
def sign_in():
    connection = None
    try:
        sign_in_form_data = request.get_json()

        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute(
            "SELECT * FROM users WHERE email = %s;",
            (sign_in_form_data["email"],)
        )

        existing_user = cursor.fetchone()

        if existing_user is None:
            return jsonify({"err": "Invalid credentials."}), 401

        password_is_valid = bcrypt.checkpw(
            sign_in_form_data["password"].encode("utf-8"),
            existing_user["password_hash"].encode("utf-8")
        )

        if not password_is_valid:
            return jsonify({"err": "Invalid credentials."}), 401

        payload = {"email": existing_user["email"], "id": existing_user["id"]}
        token = jwt.encode({"payload": payload}, os.getenv("JWT_SECRET"), algorithm="HS256")

        return jsonify({"token": token}), 200

    except Exception as err:
        return jsonify({"err": str(err)}), 500

    finally:
        if connection:
            connection.close()


# POST /auth/sign-in
# @app.route("/auth/sign-in", methods=["POST"])
# def sign_in():
#     try:
#         # Grabbing the form data/body of req
#         sign_in_form_data = request.get_json()
#         connection = get_db_connection()
#         cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
#         # Checking if user does exist in the db
#         cursor.execute(
#             "SELECT * FROM users WHERE email = %s;", (sign_in_form_data["email"],)
#         )
#         existing_user = cursor.fetchone()
#         # if no existing user, return appropriate message
#         if existing_user is None:
#             return jsonify({"err": "Invalid credentials."}), 401
#         # else check the password against the hashed version of the password
#         password_is_valid = bcrypt.checkpw(
#             bytes(sign_in_form_data["password"], "utf-8"),
#             bytes(existing_user["password_hash"], "utf-8")

#         )

#         if not password_is_valid:
#             return jsonify({"err": "Invalid credentials."}), 401
#         # Construct the payload
#         payload = {"email": existing_user["email"], "id": existing_user["id"]}
#         # Create the token, attaching the payload
#         token = jwt.encode({"payload": payload}, os.getenv("JWT_SECRET"))
#         # Send the token instead of the user
#         return jsonify({"token": token}), 200
#     except Exception as err:
#         return jsonify({"err": "Invalid credentials."}), 401
#     finally:
#         connection.close()


# Fetching all users, if authenticated
@app.route("/users")
@token_required
def users_index():
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, email FROM users;")
    users = cursor.fetchall()
    connection.close()
    return jsonify(users), 200


# Fetching specific user by id, if authenticated
@app.route("/users/<user_id>")
@token_required
def users_show(user_id):
    # Ensure that the user making the request is the same stored in the session of the g object
    if int(user_id) != g.user["id"]:
        return jsonify({"err": "Unauthorized"}), 403

    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, email FROM users WHERE id = %s;", (user_id))
    user = cursor.fetchone()
    connection.close()
    if user is None:
        return jsonify({"err": "User not found"}), 404
    return jsonify(user), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Route not found"}), 404

# Running app in debug mode (for auto-refresh)
if __name__ == '__main__':
    app.run()