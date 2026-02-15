from flask import Blueprint, jsonify, request, g
from db_helpers import get_db_connection
from auth_middleware import token_required
import psycopg2.extras
from datetime import datetime

agents_blueprint = Blueprint('agents_blueprint', __name__)

# create an agent
@agents_blueprint.route('/agents', methods=['POST'])
@token_required
def create_agent():
    try:
        data = request.get_json()
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            INSERT INTO agents (name, description, user_id, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING *;
        """, (
            data["name"],
            data.get("description"),
            g.user["id"],
            datetime.utcnow()
        ))

        created_agent = cursor.fetchone()
        connection.commit()
        connection.close()

        return jsonify(created_agent), 201

    except Exception as error:
        return jsonify({"error": str(error)}), 500
    
#get all agents
@agents_blueprint.route('/agents', methods=['GET'])
@token_required
def agents_index():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            SELECT * FROM agents
            WHERE user_id = %s;
        """, (g.user["id"],))

        agents = cursor.fetchall()
        connection.close()

        return jsonify(agents), 200

    except Exception as error:
        return jsonify({"error": str(error)}), 500

# show one agent
@agents_blueprint.route('/agents/<agent_id>', methods=['GET'])
@token_required
def agents_show(agent_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("SELECT * FROM agents WHERE id = %s;", (agent_id,))
        agent = cursor.fetchone()

        connection.close()

        if not agent:
            return jsonify({"error": "Agent not found"}), 404

        if agent["user_id"] != g.user["id"]:
            return jsonify({"error": "Unauthorized"}), 401

        return jsonify(agent), 200

    except Exception as error:
        return jsonify({"error": str(error)}), 500

#delete agent
@agents_blueprint.route('/agents/<agent_id>', methods=['DELETE'])
@token_required
def delete_agent(agent_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("SELECT * FROM agents WHERE id = %s;", (agent_id,))
        agent = cursor.fetchone()

        if not agent:
            return jsonify({"error": "Agent not found"}), 404

        if agent["user_id"] != g.user["id"]:
            return jsonify({"error": "Unauthorized"}), 401

        cursor.execute("DELETE FROM agents WHERE id = %s;", (agent_id,))
        connection.commit()
        connection.close()

        return jsonify(agent), 200

    except Exception as error:
        return jsonify({"error": str(error)}), 500
