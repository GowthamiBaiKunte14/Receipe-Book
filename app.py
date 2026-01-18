import datetime
from flask import Flask, render_template, request, redirect, url_for, g, flash
import sqlite3, os, re

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = "recipes.db"

# Save uploads inside static so Flask can serve them
UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Safe filename function (replacement for werkzeug.utils.secure_filename) ---
def secure_filename(filename):
    filename = os.path.basename(filename)  # remove path
    # replace anything not alphanumeric, dot, underscore, or hyphen
    filename = re.sub(r'[^A-Za-z0-9_.-]', '_', filename)
    return filename

# --- Database connection ---
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# --- Routes ---

@app.route("/")
def index():
    db = get_db()
    cursor = db.cursor()
    query = request.args.get("q")
    if query:
        cursor.execute(
            "SELECT * FROM recipes WHERE name LIKE ? OR ingredients LIKE ?",
            (f"%{query}%", f"%{query}%"),
        )
    else:
        cursor.execute("SELECT * FROM recipes ORDER BY name ASC")
    recipes = cursor.fetchall()
    return render_template("index.html", recipes=recipes, query=query)

@app.route("/recipe/<int:recipe_id>")
def recipe_detail(recipe_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM recipes WHERE id=?", (recipe_id,))
    recipe = cursor.fetchone()
    if not recipe:
        flash("Recipe not found!", "danger")
        return redirect(url_for("index"))
    return render_template("detail.html", recipe=recipe)

@app.route("/add", methods=["GET", "POST"])
def add_recipe():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        ingredients = request.form.get("ingredients", "").strip()
        instructions = request.form.get("instructions", "").strip()
        image_file = request.files.get("image")

        if not name or not ingredients or not instructions:
            flash("All fields are required!", "warning")
            return redirect(url_for("add_recipe"))

        image_path = None
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)
            # Store relative path (without "static/")
            image_path = os.path.relpath(image_path, "static")

        from datetime import datetime
        created_at = datetime.utcnow().isoformat()

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
        "INSERT INTO recipes (name, category, ingredients, instructions, image, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (name, category, ingredients, instructions, image_path, created_at),
        )

        db.commit()

        flash("Recipe added successfully!", "success")
        return redirect(url_for("index"))

    return render_template("add.html")

@app.route("/delete/<int:recipe_id>", methods=["POST"])
def delete_recipe(recipe_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM recipes WHERE id=?", (recipe_id,))
    db.commit()
    flash("Recipe deleted successfully!", "info")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run()
