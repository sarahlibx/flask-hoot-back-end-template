from flask import Blueprint, jsonify, request, g
from db_helpers import get_db_connection
import psycopg2
import psycopg2.extras
from auth_middleware import token_required
from db_helpers import get_db_connection, consolidate_comments_in_hoots


hoots_blueprint = Blueprint('hoots_blueprint', __name__)


@hoots_blueprint.route('/hoots', methods=['POST'])
@token_required
def create_hoot():
    try:
        new_hoot = request.get_json()
        new_hoot["author"] = g.user["id"]
        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
                        INSERT INTO hoots (author, title, text, category)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                        """,
                       (new_hoot['author'], new_hoot['title'],
                        new_hoot['text'], new_hoot['category'])
                       )
        hoot_id = cursor.fetchone()["id"]
        cursor.execute("""SELECT h.id, 
                            h.author AS hoot_author_id, 
                            h.title, 
                            h.text, 
                            h.category, 
                            u_hoot.username AS author_username
                        FROM hoots h
                        JOIN users u_hoot ON h.author = u_hoot.id
                        WHERE h.id = %s
                       """, (hoot_id,))
        created_hoot = cursor.fetchone()
        connection.commit()
        connection.close()
        return jsonify(created_hoot), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@hoots_blueprint.route('/hoots', methods=['GET'])
def hoots_index():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""SELECT h.id, h.author AS hoot_author_id, h.title, h.text, h.category, u_hoot.username AS author_username, c.id AS comment_id, c.text AS comment_text, u_comment.username AS comment_author_username
                            FROM hoots h
                            INNER JOIN users u_hoot ON h.author = u_hoot.id
                            LEFT JOIN comments c ON h.id = c.hoot
                            LEFT JOIN users u_comment ON c.author = u_comment.id;
                       """)
        hoots = cursor.fetchall()

        # Update:
        consolidated_hoots = consolidate_comments_in_hoots(hoots)

        connection.commit()
        connection.close()
        return jsonify(consolidated_hoots), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@hoots_blueprint.route('/hoots/<hoot_id>', methods=['GET'])
def show_hoot(hoot_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT h.id, h.author AS hoot_author_id, h.title, h.text, h.category, u_hoot.username AS author_username, c.id AS comment_id, c.text AS comment_text, u_comment.username AS comment_author_username
            FROM hoots h
            INNER JOIN users u_hoot ON h.author = u_hoot.id
            LEFT JOIN comments c ON h.id = c.hoot
            LEFT JOIN users u_comment ON c.author = u_comment.id
            WHERE h.id = %s;""",
                       (hoot_id,))
        unprocessed_hoot = cursor.fetchall()
        if unprocessed_hoot is not None:
            processed_hoot = consolidate_comments_in_hoots(unprocessed_hoot)[0]
            connection.close()
            return jsonify(processed_hoot), 200
        else:
            connection.close()
            return jsonify({"error": "Hoot not found"}), 404
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@hoots_blueprint.route('/hoots/<hoot_id>', methods=['PUT'])
@token_required
def update_hoot(hoot_id):
    try:
        updated_hoot_data = request.json
        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM hoots WHERE hoots.id = %s", (hoot_id,))
        hoot_to_update = cursor.fetchone()
        if hoot_to_update is None:
            return jsonify({"error": "hoot not found"}), 404
        connection.commit()
        if hoot_to_update["author"] is not g.user["id"]:
            return jsonify({"error": "Unauthorized"}), 401
        cursor.execute("UPDATE hoots SET title = %s, text = %s, category = %s WHERE hoots.id = %s RETURNING *",
                       (updated_hoot_data["title"], updated_hoot_data["text"], updated_hoot_data["category"], hoot_id))
        hoot_id = cursor.fetchone()["id"]
        cursor.execute("""SELECT h.id, 
                            h.author AS hoot_author_id, 
                            h.title, 
                            h.text, 
                            h.category, 
                            u_hoot.username AS author_username
                        FROM hoots h
                        JOIN users u_hoot ON h.author = u_hoot.id
                        WHERE h.id = %s
                       """, (hoot_id,))
        updated_hoot = cursor.fetchone()
        connection.commit()
        connection.close()
        return jsonify(updated_hoot), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@hoots_blueprint.route('/hoots/<hoot_id>', methods=['DELETE'])
@token_required
def delete_hoot(hoot_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM hoots WHERE hoots.id = %s", (hoot_id,))
        hoot_to_delete = cursor.fetchone()
        if hoot_to_delete is None:
            return jsonify({"error": "hoot not found"}), 404
        connection.commit()
        if hoot_to_delete["author"] is not g.user["id"]:
            return jsonify({"error": "Unauthorized"}), 401
        cursor.execute("DELETE FROM hoots WHERE hoots.id = %s", (hoot_id,))
        connection.commit()
        connection.close()
        return jsonify(hoot_to_delete), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500
