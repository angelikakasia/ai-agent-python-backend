from flask import Blueprint, jsonify, request, g, Response
from db_helpers import get_db_connection
from auth_middleware import token_required
import psycopg2.extras
from datetime import datetime
import json

agents_blueprint = Blueprint("agents_blueprint", __name__)

# ======================================
# Helper: Calculate Impact Summary
# ======================================

def calculate_impact(cursor, agent_id):
    cursor.execute("""
        SELECT a.impact_level, COUNT(*) as count
        FROM permissions p
        JOIN actions a ON p.action_id = a.id
        WHERE p.agent_id = %s
        GROUP BY a.impact_level;
    """, (agent_id,))

    rows = cursor.fetchall()

    summary = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "irreversible": 0
    }

    for row in rows:
        summary[row["impact_level"]] = row["count"]

    return summary


# ======================================
# Helper: Calculate Risk Score
# ======================================

def calculate_risk_score(impact_summary):
    weights = {
        "low": 1,
        "medium": 3,
        "high": 6,
        "irreversible": 10
    }

    score = 0
    for level, count in impact_summary.items():
        score += weights[level] * count

    return score


# ======================================
# CREATE AGENT
# ======================================

@agents_blueprint.route("/agents", methods=["POST"])
@token_required
def create_agent():
    try:
        data = request.get_json()
        if not data or "name" not in data:
            return jsonify({"error": "Name is required"}), 400

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


# ======================================
# GET ALL AGENTS
# ======================================

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


# ======================================
# SHOW ONE AGENT
# ======================================

@agents_blueprint.route("/agents/<agent_id>", methods=["GET"])
@token_required
def agents_show(agent_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Verify ownership
        cursor.execute("""
            SELECT * FROM agents
            WHERE id = %s AND user_id = %s;
        """, (agent_id, g.user["id"]))

        agent = cursor.fetchone()

        if not agent:
            connection.close()
            return jsonify({"error": "Agent not found or unauthorized"}), 404

        # Get actions
        cursor.execute("""
            SELECT a.*
            FROM permissions p
            JOIN actions a ON p.action_id = a.id
            WHERE p.agent_id = %s;
        """, (agent_id,))

        actions = cursor.fetchall()

        impact_summary = calculate_impact(cursor, agent_id)
        risk_score = calculate_risk_score(impact_summary)

        connection.close()

        return jsonify({
            "agent": agent,
            "actions": actions,
            "impact_summary": impact_summary,
            "risk_score": risk_score
        }), 200

    except Exception as error:
        return jsonify({"error": str(error)}), 500


# ======================================
# DELETE AGENT
# ======================================

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

        if not deleted:
            connection.close()
            return jsonify({"error": "Agent not found or unauthorized"}), 404

        connection.commit()
        connection.close()

        return jsonify({"message": "Agent deleted"}), 200

    except Exception as error:
        return jsonify({"error": str(error)}), 500


# ======================================
# ASSIGN ACTION
# ======================================

@agents_blueprint.route("/agents/<agent_id>/actions", methods=["POST"])
@token_required
def assign_action(agent_id):
    try:
        data = request.get_json()
        if not data or "action_id" not in data:
            return jsonify({"error": "action_id is required"}), 400

        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Verify agent ownership
        cursor.execute("""
            SELECT 1 FROM agents
            WHERE id = %s AND user_id = %s;
        """, (agent_id, g.user["id"]))

        if not cursor.fetchone():
            connection.close()
            return jsonify({"error": "Agent not found or unauthorized"}), 404

        # Insert permission (avoid duplicates at DB level if possible)
        cursor.execute("""
            INSERT INTO permissions (agent_id, action_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (agent_id, data["action_id"]))

        connection.commit()

        impact_summary = calculate_impact(cursor, agent_id)
        connection.close()

        return jsonify({
            "message": "Action assigned",
            "impact_summary": impact_summary
        }), 201

    except Exception as error:
        return jsonify({"error": str(error)}), 500


# ======================================
# REMOVE ACTION
# ======================================

@agents_blueprint.route("/agents/<agent_id>/actions/<action_id>", methods=["DELETE"])
@token_required
def remove_action(agent_id, action_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            DELETE FROM permissions
            WHERE agent_id = %s AND action_id = %s
            RETURNING *;
        """, (agent_id, action_id))

        if not cursor.fetchone():
            connection.close()
            return jsonify({"error": "Permission not found"}), 404

        connection.commit()

        impact_summary = calculate_impact(cursor, agent_id)
        connection.close()

        return jsonify({
            "message": "Action removed",
            "impact_summary": impact_summary
        }), 200

    except Exception as error:
        return jsonify({"error": str(error)}), 500


# ======================================
# EXPORT AGENT
# ======================================

@agents_blueprint.route("/agents/<agent_id>/export", methods=["GET"])
@token_required
def export_agent(agent_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            SELECT * FROM agents
            WHERE id = %s AND user_id = %s;
        """, (agent_id, g.user["id"]))

        agent = cursor.fetchone()

        if not agent:
            connection.close()
            return jsonify({"error": "Agent not found or unauthorized"}), 404

        cursor.execute("""
            SELECT a.*
            FROM permissions p
            JOIN actions a ON p.action_id = a.id
            WHERE p.agent_id = %s;
        """, (agent_id,))

        actions = cursor.fetchall()

        impact_summary = calculate_impact(cursor, agent_id)
        risk_score = calculate_risk_score(impact_summary)

        connection.close()

        export_data = {
            "agent": agent,
            "actions": actions,
            "impact_summary": impact_summary,
            "risk_score": risk_score
        }

        response = Response(
            json.dumps(export_data, default=str),
            mimetype="application/json"
        )

        response.headers["Content-Disposition"] = "attachment; filename=agent_export.json"

        return response

    except Exception as error:
        return jsonify({"error": str(error)}), 500
