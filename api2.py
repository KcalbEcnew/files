from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import sqlite3
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'fresh.db')

# Helper function to get a database connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This allows fetching results as dictionaries
    return conn

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
def add_recipe():
    data = request.get_json()  # Get the JSON data from the request
   
    # Validate the JSON data
    if not data or 'name' not in data or 'description' not in data or "user_id":
        return jsonify({"error": "Invalid data. 'name' and 'description' are required fields."}), 400
   
    name = data['name']
    description = data['description']
    user_id = user_id['user_id']

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
   
    # Insert the new trivia into the database
    cursor.execute("INSERT INTO recipe (name, description) VALUES (?, ?)", (name, description))
    conn.commit()  # Save (commit) the changes to the database
    conn.close()
   
    return jsonify({"message": "New trivia added successfully!"}), 201
 
 
#API - 4
# New route to update trivia for a specific superhero
@app.route('/updatetrivia/<hero_name>', methods=['PUT'])
def update_trivia_for_hero(hero_name):
    data = request.get_json()
   
    # Validate the input data
    if not data or 'question' not in data or 'answer' not in data:
        return jsonify({"error": "Invalid data. 'question' and 'answer' are required fields."}), 400
   
    question = data['question']
    answer = data['answer']
 
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
 
    # Update trivia for the specified superhero
    cursor.execute("UPDATE trivia SET question = ?, answer = ? WHERE hero = ?", (question, answer, hero_name))
    rows_updated = cursor.rowcount  # Get the number of rows updated
    conn.commit()  # Save changes
    conn.close()
   
    if rows_updated > 0:
        return jsonify({"message": f"Updated trivia for '{hero_name}'", "rows_updated": rows_updated}), 200
    else:
        return jsonify({"error": f"No trivia found for superhero '{hero_name}'."}), 404


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
