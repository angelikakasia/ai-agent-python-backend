from flask import Blueprint, jsonify, request, g
from db_helpers import get_db_connection
from auth_middleware import token_required
import psycopg2.extras
from datetime import datetime

agents_blueprint = Blueprint("agents_blueprint", __name__)

# CREATE AGENT
@agents_blueprint.route("/agents", methods=["POST"])
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

        new_agent = cursor.fetchone()
        connection.commit()
        connection.close()

        return jsonify(new_agent), 201

    except Exception as error:
        return jsonify({"error": str(error)}), 500


# GET ALL AGENTS (USER ONLY)
@agents_blueprint.route("/agents", methods=["GET"])
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



# SHOW ONE AGENT
@agents_blueprint.route('/agents/<agent_id>', methods=['GET'])
@token_required
def agents_show(agent_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Get agent
        cursor.execute("SELECT * FROM agents WHERE id = %s;", (agent_id,))
        agent = cursor.fetchone()

        if not agent:
            connection.close()
            return jsonify({"error": "Agent not found"}), 404

        if agent["user_id"] != g.user["id"]:
            connection.close()
            return jsonify({"error": "Unauthorized"}), 401

        # Get assigned actions
        cursor.execute("""
            SELECT a.*
            FROM permissions p
            JOIN actions a ON p.action_id = a.id
            WHERE p.agent_id = %s;
        """, (agent_id,))

        actions = cursor.fetchall()

        # Impact summary
        impact_summary = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "irreversible": 0
        }

        for action in actions:
            impact_summary[action["impact_level"]] += 1

        connection.close()

        return jsonify({
            "agent": agent,
            "actions": actions,
            "impact_summary": impact_summary
        }), 200

    except Exception as error:
        return jsonify({"error": str(error)}), 500

# GET all available actions
@agents_blueprint.route('/actions', methods=['GET'])
@token_required
def actions_index():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("SELECT * FROM actions;")
        actions = cursor.fetchall()

        connection.close()
        return jsonify(actions), 200

    except Exception as error:
        return jsonify({"error": str(error)}), 500



# UPDATE AGENT
@agents_blueprint.route("/agents/<agent_id>", methods=["PUT"])
@token_required
def update_agent(agent_id):
    try:
        data = request.get_json()

        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            UPDATE agents
            SET name = %s,
                description = %s
            WHERE id = %s AND user_id = %s
            RETURNING *;
        """, (
            data["name"],
            data.get("description"),
            agent_id,
            g.user["id"]
        ))

        updated = cursor.fetchone()
        connection.commit()
        connection.close()

        if not updated:
            return jsonify({"error": "Agent not found or unauthorized"}), 404

        return jsonify(updated), 200

    except Exception as error:
        return jsonify({"error": str(error)}), 500



# DELETE AGENT
@agents_blueprint.route("/agents/<agent_id>", methods=["DELETE"])
@token_required
def delete_agent(agent_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            DELETE FROM agents
            WHERE id = %s AND user_id = %s
            RETURNING *;
        """, (agent_id, g.user["id"]))

        deleted = cursor.fetchone()
        connection.commit()
        connection.close()

        if not deleted:
            return jsonify({"error": "Agent not found or unauthorized"}), 404

        return jsonify(deleted), 200

    except Exception as error:
        return jsonify({"error": str(error)}), 500

# ASSIGN ACTION TO AGENT
@agents_blueprint.route("/agents/<agent_id>/actions", methods=["POST"])
@token_required
def assign_action(agent_id):
    try:
        data = request.get_json()

        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 1 Verify agent exists and belongs to logged-in user
        cursor.execute("""
            SELECT * FROM agents
            WHERE id = %s AND user_id = %s;
        """, (agent_id, g.user["id"]))

        agent = cursor.fetchone()

        if not agent:
            connection.close()
            return jsonify({"error": "Agent not found or unauthorized"}), 404

        # 2 Verify action exists
        cursor.execute("""
            SELECT * FROM actions
            WHERE id = %s;
        """, (data["action_id"],))

        action = cursor.fetchone()

        if not action:
            connection.close()
            return jsonify({"error": "Action not found"}), 404

        # 3 Prevent duplicate permission
        cursor.execute("""
            SELECT * FROM permissions
            WHERE agent_id = %s AND action_id = %s;
        """, (agent_id, data["action_id"]))

        existing_permission = cursor.fetchone()

        if existing_permission:
            connection.close()
            return jsonify({"error": "Action already assigned"}), 400

        # 4 Insert permission
        cursor.execute("""
            INSERT INTO permissions (agent_id, action_id)
            VALUES (%s, %s)
            RETURNING *;
        """, (agent_id, data["action_id"]))

        connection.commit()

        # 5 Return updated actions list
        cursor.execute("""
            SELECT a.*
            FROM permissions p
            JOIN actions a ON p.action_id = a.id
            WHERE p.agent_id = %s;
        """, (agent_id,))

        actions = cursor.fetchall()

        connection.close()

        return jsonify({
            "message": "Action assigned",
            "actions": actions
        }), 201

    except Exception as error:
        return jsonify({"error": str(error)}), 500



# REMOVE ACTION
@agents_blueprint.route("/agents/<agent_id>/actions/<action_id>", methods=["DELETE"])
@token_required
def remove_action(agent_id, action_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 1 Check agent exists
        cursor.execute("SELECT * FROM agents WHERE id = %s;", (agent_id,))
        agent = cursor.fetchone()

        if not agent:
            connection.close()
            return jsonify({"error": "Agent not found"}), 404

        # 2 Check ownership
        if agent["user_id"] != g.user["id"]:
            connection.close()
            return jsonify({"error": "Unauthorized"}), 401

        # 3 Delete permission
        cursor.execute("""
            DELETE FROM permissions
            WHERE agent_id = %s AND action_id = %s
            RETURNING *;
        """, (agent_id, action_id))

        deleted = cursor.fetchone()

        if not deleted:
            connection.close()
            return jsonify({"error": "Permission not found"}), 404

        connection.commit()
        connection.close()

        return jsonify(deleted), 200

    except Exception as error:
        return jsonify({"error": str(error)}), 500

