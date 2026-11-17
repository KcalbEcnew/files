from functools import wraps
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import random
import sqlite3
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'fresh.db')
app.secret_key = os.urandom(24)

# Helper function to get a database connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This allows fetching results as dictionaries
    return conn

def login_required(f):
    """Decorator to enforce active session on endpoints."""    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized. Please log in first."}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')


    if not 'username' or not 'password': 
        return jsonify({"error": "data missing. 'username', and 'password' are required fields."}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM User WHERE username = ? AND password = ?",(username,password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user_id'] = user['user_id']
        session['username'] = user["username"]
    
        return jsonify({"message": f"Logged in successfully as {user['username']}","user_id": user['user_id']}), 200
    else:
        return jsonify({"error": "Invalid username or password."}), 401

@app.route('/register',methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    bio = data.get('bio')

    if not 'username' or not 'password': 
        return jsonify({"error": "data missing. 'username', and 'password' are required fields."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM User WHERE username = ? AND password = ?',(username,password))
    user_id = cursor.fetchone()
    if user_id == None:
        cursor.execute("INSERT into User (username,password,bio) VALUES (?,?,?)",(username,password,bio))
        conn.commit()
        conn.close()
        return(jsonify({"message": f"New User Created as as {username}"})), 200
    else:
        conn.close()
        return(jsonify({"error" : f"account with username {username} exists"}))


#####API 1
# Route to get a random trivia question from the8 database
@app.route('/randomrecipe', methods=['GET'])
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
 
#API 2
# Route to get trivia for a specific superhero
@app.route("/recipes/search", methods=["GET"])
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
 
 
#API 3
# Route to add a new trivia entry to the database
@app.route('/addrecipe', methods=['POST'])
@login_required
def add_recipe():
    data = request.get_json()  # Get the JSON data from the request
   
    # Validate the JSON data
    if not data or 'name' not in data or 'description' not in data:
        return jsonify({"error": "Invalid data. 'name', 'description' and 'user_id' are required fields."}), 400
   
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
   
    return jsonify({"message": "New trivia added successfully!"}), 201
 

 
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

#API 2
# Route to get trivia for a specific superhero
@app.route("/cooklists/search", methods=["GET"])
def search_Cooklists():
    query = request.args.get("name", "")
 
    conn = get_db_connection()
# Ensure rows are returned as dictionary-like objects
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
 
    cursor.execute("SELECT * FROM Cooklist WHERE name LIKE ?", (f"%{query}%",))
    Cooklists = cursor.fetchall()
    conn.close()
 
    # Convert sqlite3.Row objects into standard dictionaries
    Cooklist_list = [dict(row) for row in Cooklists]
    return jsonify(Cooklist_list), 200
 
 
#API 3
# Route to add a new trivia entry to the database
@app.route('/addCooklist', methods=['POST'])
@login_required
def add_Cooklist():
    data = request.get_json()  # Get the JSON data from the request
   
    # Validate the JSON data
    if not data or 'name' not in data or 'description' not in data:
        return jsonify({"error": "Invalid data. 'name', 'description' and 'user_id' are required fields."}), 400
   
    name = data['name']
    description = data['description']
    user_id = session['user_id']

    if not user_id:
        return jsonify({"error" :"user has not logged in"})

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
   
    # Insert the new trivia into the database
    cursor.execute("INSERT INTO Cooklist (name, description, user_id) VALUES (?, ?, ?)", (name, description, user_id))
    conn.commit()  # Save (commit) the changes to the database
    conn.close()
   
    return jsonify({"message": "New trivia added successfully!"}), 201
 
 


 
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


@app.route('/addsavedrecipes', methods=['POST'])
@login_required
def add_savedrecipes():
    data = request.get_json()  # Get the JSON data from the request
   
    # Validate the JSON data
    if not data or 'recipe_id' not in data or 'cooklist_name' not in data:
        return jsonify({"error": "Invalid data. 'recipe_id', 'cooklist_name' and 'user_id' are required fields."}), 400
   
    recipe_id = data['recipe_id']
    user_id = session['user_id']

    if not user_id:
        return jsonify({"error" :"user has not logged in"})

    cooklist_name = data['cooklist_name'] 
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
# Ensure rows are returned as dictionary-like objects
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Cooklist WHERE name = ?", (cooklist_name,))
    cooklist_raw = cursor.fetchall()
    cooklist_dict = [dict(row) for row in cooklist_raw]
    cooklist_list = cooklist_dict[0]
    cooklist_id = cooklist_list['cooklist_id']
    cooklist_name = cooklist_list['name']

    cursor.execute("INSERT INTO saved_recipies (recipe_id, cooklist_id, user_id) VALUES (?, ?, ?)", (recipe_id, cooklist_id, user_id))
    conn.commit()  # Save (commit) the changes to the database
    conn.close()
   
    return jsonify({"message": f"Added recipe into cooklist '{cooklist_name}'"}), 201



# Quiz mode endpoint
@app.route('/quiz', methods=['GET', 'POST'])
def quiz_mode():
    if request.method == 'GET':
        # TODO: Connect to the database and fetch a list of trivia questions
        # conn = (Connect to the database)
        # cursor = (Create a cursor from the connection)
        # cursor.execute("SELECT * FROM trivia")  # Query to fetch trivia questions
        # trivia_list = (Fetch all trivia questions)
        # conn.close()  # Close the database connection

        # TODO: Check if trivia_list contains questions
        # if trivia_list:
            # TODO: Select a random trivia question and return it as JSON (excluding the answer)
            # trivia = (Select a random trivia item from trivia_list)
            # return jsonify({"Superhero": (Superhero name), "Question": (Question text)})
        # else:
            # TODO: Return a 404 error if no trivia is found in the database
            # return jsonify({"error": "No trivia found in the database."}), 404
        print()

    elif request.method == 'POST':
        # TODO: Retrieve JSON data from the request
        # data = (Get JSON data from the request)
        # hero = (Extract 'hero' from data)
        # user_answer = (Extract 'answer' from data)

        # TODO: Validate that both 'hero' and 'answer' fields are present
        # if (Check if hero or user_answer is missing):
            # return jsonify({"error": "Hero and answer are required fields."}), 400

        # TODO: Connect to the database and fetch the correct answer for the given hero
        # conn = (Connect to the database)
        # cursor = (Create a cursor from the connection)
        # cursor.execute("SELECT * FROM trivia WHERE hero = ?", (hero,))
        # trivia = (Fetch one trivia item for the specified hero)
        # conn.close()  # Close the database connection

        # TODO: Check if trivia is found for the given hero
        # if trivia:
            # correct_answer = (Retrieve correct answer from trivia item)
            # TODO: Compare the user's answer to the correct answer (case insensitive)
            # if (User answer matches correct answer):
                # return jsonify({"result": "Correct!", "correct_answer": correct_answer})
            # else:
                # return jsonify({"result": "Incorrect", "correct_answer": correct_answer})
        # else:
            # TODO: Return a 404 error if no trivia is found for the specified hero
            # return jsonify({"error": f"No trivia found for superhero '{hero}'."}), 404
            print()



# Start the Flask server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)
