
import os
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)


# --------------------------------------------------
# Database configuration
# --------------------------------------------------

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "notesdb")


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


# --------------------------------------------------
# Initialize database
# --------------------------------------------------

def init_db():
    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL
            )
        """)

        connection.commit()
        cursor.close()

    finally:
        connection.close()


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    try:
        connection = get_db_connection()
        connection.close()

        return jsonify({
            "status": "healthy",
            "database": "connected"
        }), 200

    except Exception as error:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(error)
        }), 503


# --------------------------------------------------
# Get all notes
# --------------------------------------------------

@app.route("/notes", methods=["GET"])
def get_notes():

    connection = get_db_connection()

    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT id, title, content
            FROM notes
            ORDER BY id
        """)

        notes = cursor.fetchall()

        cursor.close()

        return jsonify(notes), 200

    finally:
        connection.close()


# --------------------------------------------------
# Get one note
# --------------------------------------------------

@app.route("/notes/<int:note_id>", methods=["GET"])
def get_note(note_id):

    connection = get_db_connection()

    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT id, title, content
            FROM notes
            WHERE id = %s
        """, (note_id,))

        note = cursor.fetchone()

        cursor.close()

        if note is None:
            return jsonify({
                "error": "Note not found"
            }), 404

        return jsonify(note), 200

    finally:
        connection.close()


# --------------------------------------------------
# Create note
# --------------------------------------------------

@app.route("/notes", methods=["POST"])
def create_note():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON body required"
        }), 400

    title = data.get("title")
    content = data.get("content")

    if not title or not content:
        return jsonify({
            "error": "title and content are required"
        }), 400

    connection = get_db_connection()

    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            INSERT INTO notes (title, content)
            VALUES (%s, %s)
            RETURNING id, title, content
        """, (title, content))

        note = cursor.fetchone()

        connection.commit()

        cursor.close()

        return jsonify(note), 201

    finally:
        connection.close()


# --------------------------------------------------
# Delete note
# --------------------------------------------------

@app.route("/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM notes
            WHERE id = %s
        """, (note_id,))

        deleted = cursor.rowcount

        connection.commit()

        cursor.close()

        if deleted == 0:
            return jsonify({
                "error": "Note not found"
            }), 404

        return jsonify({
            "message": "Note deleted successfully"
        }), 200

    finally:
        connection.close()


# --------------------------------------------------
# Application startup
# --------------------------------------------------

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5002
    )
