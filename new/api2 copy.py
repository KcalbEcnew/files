"""Fresh recipe API, connected to ui (2).html.
Install: python3 -m pip install flask flask-cors
Run: python3 "api2 copy.py"; open http://localhost:5555.
fresh.db is created on first run. Set SECRET_KEY for sessions to survive restarts.
All recipe/cook-list features require login. Passwords are stored as hashes.
"""
from functools import wraps
from flask import Flask, jsonify, request, session, send_file
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import random
import sqlite3
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'fresh.db')
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This allows fetching results as dictionaries
    return conn



def init_db():
    conn = get_db_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS User (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, bio TEXT
        );
        CREATE TABLE IF NOT EXISTS recipe (
            recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, description TEXT NOT NULL, user_id INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS Cooklist (
            cooklist_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, description TEXT NOT NULL, user_id INTEGER NOT NULL,
            UNIQUE(user_id, name)
        );
        CREATE TABLE IF NOT EXISTS saved_recipies (
            recipe_id INTEGER, cooklist_id INTEGER, user_id INTEGER,
            PRIMARY KEY (recipe_id, cooklist_id, user_id)
        );
        CREATE TRIGGER IF NOT EXISTS cleanup_recipe_links AFTER DELETE ON recipe
        BEGIN DELETE FROM saved_recipies WHERE recipe_id = OLD.recipe_id; END;
        CREATE TRIGGER IF NOT EXISTS cleanup_cooklist_links AFTER DELETE ON Cooklist
        BEGIN DELETE FROM saved_recipies WHERE cooklist_id = OLD.cooklist_id; END;
    """)
    conn.commit()
    conn.close()

def credentials():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    if not all(isinstance(data.get(k), str) and data[k].strip() for k in ('username', 'password')):
        return None
    return data['username'].strip(), data['password']


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Please log in first.'}), 401
        return f(*args, **kwargs)
    return decorated


@app.route('/register', methods=['POST'])
def create_user():
    values = credentials()
    if values is None:
        return jsonify({'error': 'Username and password are required.'}), 400
    username, password = values
    bio = request.get_json().get('bio', '')
    if not isinstance(bio, str):
        return jsonify({'error': 'Bio must be text.'}), 400
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO User (username, password, bio) VALUES (?, ?, ?)',
                     (username, generate_password_hash(password), bio))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists.'}), 409
    finally:
        conn.close()
    return jsonify({'message': 'Account created. Please log in.'}), 201


@app.route('/login', methods=['POST'])
def login():
    values = credentials()
    if values is None:
        return jsonify({'error': 'Username and password are required.'}), 400
    username, password = values
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM User WHERE username = ?', (username,)).fetchone()
    conn.close()
    if user is None or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid username or password.'}), 401
    session.clear()
    session['user_id'] = user['user_id']
    session['username'] = user['username']
    return jsonify({'message': 'Logged in successfully.', 'user_id': user['user_id'], 'username': user['username']})


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return jsonify({'message': 'Logged out.'})


@app.route('/me', methods=['GET'])
def me():
    if 'user_id' not in session:
        return jsonify({'logged_in': False}), 401
    return jsonify({'logged_in': True, 'user_id': session['user_id'], 'username': session['username']})


@app.route('/addsavedrecipes', methods=['POST'])
@login_required
def add_savedrecipes():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Send a JSON object.'}), 400
    recipe_id, cooklist_name = data.get('recipe_id'), data.get('cooklist_name')
    if type(recipe_id) is not int or recipe_id <= 0 or not isinstance(cooklist_name, str) or not cooklist_name.strip():
        return jsonify({'error': 'A positive recipe_id and cooklist_name are required.'}), 400
    conn = get_db_connection()
    try:
        recipe = conn.execute('SELECT 1 FROM recipe WHERE recipe_id = ?', (recipe_id,)).fetchone()
        cooklist = conn.execute('SELECT cooklist_id FROM Cooklist WHERE name = ? AND user_id = ?',
                                (cooklist_name, session['user_id'])).fetchone()
        if recipe is None or cooklist is None:
            return jsonify({'error': 'Recipe or cook list not found.'}), 404
        conn.execute('INSERT OR IGNORE INTO saved_recipies (recipe_id,cooklist_id,user_id) VALUES (?,?,?)',
                     (recipe_id, cooklist['cooklist_id'], session['user_id']))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'message': f'Recipe saved to {cooklist_name}.'}), 201


@app.route('/randomrecipe', methods=['GET'])
@login_required
def get_recipe_db():
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
   
    # Fetch all trivia questions from the database
    cursor.execute("SELECT * FROM recipe")
    recipe_list = cursor.fetchall()
   
    # Close the database connection
    conn.close()
   
    if recipe_list:
        # Select a random trivia question from the list
        recipe = random.choice(recipe_list)
        return jsonify({"Name": recipe["name"], "Description": recipe["description"]})
    else:
        return jsonify({"error": "No recipes found in database."}), 404


@app.route("/recipes/search", methods=["GET"])
@login_required
def search_recipes():
    query = request.args.get("name", "")
 
    conn = get_db_connection()
# Ensure rows are returned as dictionary-like objects
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
 
    cursor.execute("SELECT * FROM recipe WHERE name LIKE ?", (f"%{query}%",))
    recipes = cursor.fetchall()
    conn.close()
 
    # Convert sqlite3.Row objects into standard dictionaries
    recipe_list = [dict(row) for row in recipes]
    return jsonify(recipe_list), 200


@app.route('/addrecipe', methods=['POST'])
@login_required
def add_recipe():
    data = request.get_json()  # Get the JSON data from the request
   
    # Validate the JSON data
    if not isinstance(data, dict) or not all(isinstance(data.get(k), str) and data[k].strip() for k in ('name', 'description')):
        return jsonify({"error": "Invalid data. 'name' and 'description' are required fields."}), 400
   
    name = data['name']
    description = data['description']
    user_id = session['user_id']

    if not user_id:
        return jsonify({"error" :"user has not logged in"})

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
   
    # Insert the new trivia into the database
    cursor.execute("INSERT INTO recipe (name, description, user_id) VALUES (?, ?, ?)", (name, description, user_id))
    conn.commit()  # Save (commit) the changes to the database
    conn.close()
   
    return jsonify({"message": "Recipe added successfully!"}), 201


@app.route("/deleterecipe", methods=["DELETE"])
@login_required
def delete_recipe():  # Renamed from search_recipes
    data = request.get_json()
 
    # 1. Fixed validation and error message
    if not data or "recipe_id" not in data:
        return (
            jsonify({"error": "Invalid request. 'recipe_id' is required."}),
            400,
        )
 
    recipe_id = data["recipe_id"]
    user_id = session['user_id']

    if not user_id:
        return jsonify({"error" :"user has not logged in"})


    conn = get_db_connection()
    cursor = conn.cursor()
 
    try:
        # 2. Fixed SQL syntax and tuple formatting
        cursor.execute(
            "DELETE FROM recipe WHERE recipe_id = ? AND user_id = ?", (recipe_id,user_id)
        )
 
        # 3. Check if a row was actually deleted
        if cursor.rowcount == 0:
            return (
                jsonify(
                    {"error": f"No recipe found with recipe_id {recipe_id}."}
                ),
                404,
            )
 
        # 4. Commit changes to save deletion
        conn.commit()
 
        # 5. Fixed HTTP status code to 200 OK
        return jsonify({"message": "Recipe deleted successfully"}), 200
 
    except Exception as e:
        conn.rollback()
        return jsonify({"error": "Failed to delete recipe"}), 500
 
    finally:
        conn.close()


@app.route("/cooklists/search", methods=["GET"])
@login_required
def search_Cooklists():
    query = request.args.get("name", "")
 
    conn = get_db_connection()
# Ensure rows are returned as dictionary-like objects
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
 
    cursor.execute("SELECT * FROM Cooklist WHERE name LIKE ? AND user_id = ?", (f"%{query}%", session["user_id"]))
    Cooklists = cursor.fetchall()
    conn.close()
 
    # Convert sqlite3.Row objects into standard dictionaries
    Cooklist_list = [dict(row) for row in Cooklists]
    return jsonify(Cooklist_list), 200


@app.route('/addCooklist', methods=['POST'])
@login_required
def add_Cooklist():
    data = request.get_json()  # Get the JSON data from the request
   
    # Validate the JSON data
    if not isinstance(data, dict) or not all(isinstance(data.get(k), str) and data[k].strip() for k in ('name', 'description')):
        return jsonify({"error": "Invalid data. 'name' and 'description' are required fields."}), 400
   
    name = data['name']
    description = data['description']
    user_id = session['user_id']

    if not user_id:
        return jsonify({"error" :"user has not logged in"})

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
   
    # Insert the new trivia into the database
    try:
        cursor.execute("INSERT INTO Cooklist (name, description, user_id) VALUES (?, ?, ?)", (name, description, user_id))
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "You already have a cook list with that name."}), 409
    conn.commit()  # Save (commit) the changes to the database
    conn.close()
   
    return jsonify({"message": "Cook list added successfully!"}), 201


@app.route("/deleteCooklist", methods=["DELETE"])
@login_required
def delete_Cooklist():  # Renamed from search_Cooklists
    data = request.get_json()
 
    # 1. Fixed validation and error message
    if not data or "Cooklist_id" not in data:
        return (
            jsonify({"error": "Invalid request. 'Cooklist_id' is required."}),
            400,
        )
 
    Cooklist_id = data["Cooklist_id"]
    user_id = session['user_id']

    if not user_id:
        return jsonify({"error" :"user has not logged in"})

 
    conn = get_db_connection()
    cursor = conn.cursor()
 
    try:
        # 2. Fixed SQL syntax and tuple formatting
        cursor.execute(
            "DELETE FROM Cooklist WHERE Cooklist_id = ? AND user_id = ?", (Cooklist_id,user_id)
        )
 
        # 3. Check if a row was actually deleted
        if cursor.rowcount == 0:
            return (
                jsonify(
                    {"error": f"No Cooklist found with Cooklist_id {Cooklist_id}."}
                ),
                404,
            )
 
        # 4. Commit changes to save deletion
        conn.commit()
 
        # 5. Fixed HTTP status code to 200 OK
        return jsonify({"message": "Cooklist deleted successfully"}), 200
 
    except Exception as e:
        conn.rollback()
        return jsonify({"error": "Failed to delete Cooklist"}), 500
 
    finally:
        conn.close()


# Provided UI support: show/remove saved recipes, using the existing join table.
@app.route('/cooklists/<int:cooklist_id>/recipes', methods=['GET'])
@login_required
def list_saved_recipes(cooklist_id):
    conn = get_db_connection()
    own = conn.execute('SELECT 1 FROM Cooklist WHERE cooklist_id=? AND user_id=?',
                       (cooklist_id, session['user_id'])).fetchone()
    if not own:
        conn.close()
        return jsonify({'error': 'Cook list not found.'}), 404
    rows = conn.execute("""SELECT recipe.* FROM recipe JOIN saved_recipies USING(recipe_id)
                           WHERE cooklist_id=? AND saved_recipies.user_id=?""",
                        (cooklist_id, session['user_id'])).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route('/cooklists/<int:cooklist_id>/recipes/<int:recipe_id>', methods=['DELETE'])
@login_required
def remove_saved_recipe(cooklist_id, recipe_id):
    conn = get_db_connection()
    result = conn.execute('DELETE FROM saved_recipies WHERE cooklist_id=? AND recipe_id=? AND user_id=?',
                          (cooklist_id, recipe_id, session['user_id']))
    conn.commit()
    conn.close()
    if not result.rowcount:
        return jsonify({'error': 'Saved recipe not found.'}), 404
    return jsonify({'message': 'Recipe removed from cook list.'})


@app.route('/')
def ui():
    return send_file(os.path.join(BASE_DIR, 'ui (2).html'))


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5555)
