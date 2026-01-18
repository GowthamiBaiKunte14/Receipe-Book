# init_db.py
"""
Initialize the SQLite database for Recipe Book.

Creates:
 - users (id, username, email, password_hash, created_at)
 - recipes (id, name, category, ingredients, instructions, cooking_time, image, user_id, created_at)

Run:
    python init_db.py
"""

import sqlite3
import os
from datetime import datetime
try:
    from werkzeug.security import generate_password_hash
except Exception:
    # If Werkzeug is not available, use a simple fallback (NOT recommended for production).
    import hashlib
    def generate_password_hash(password, method='pbkdf2:sha256', salt_length=8):
        # Very minimal fallback: not recommended for real apps.
        salt = os.urandom(salt_length).hex()
        h = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
        return f"fallback${salt}${h}"

DB_FILE = "recipes.db"

def main():
    # remove existing DB if present (optional)
    if os.path.exists(DB_FILE):
        print(f"Removing existing database '{DB_FILE}'")
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Enable foreign keys
    cur.execute("PRAGMA foreign_keys = ON;")

    # Create users table
    cur.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # Create recipes table
    cur.execute("""
    CREATE TABLE recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,         -- e.g., 'Vegetarian', 'Non-Vegetarian', 'Snacks'
        ingredients TEXT NOT NULL,
        instructions TEXT NOT NULL,
        cooking_time TEXT,              -- e.g., "30 mins"
        image TEXT,                     -- path relative to static/, e.g. 'uploads/tea.jpg'
        user_id INTEGER,                -- who added the recipe (nullable)
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # Indexes to speed up search by name/category
    cur.execute("CREATE INDEX idx_recipes_name ON recipes(name);")
    cur.execute("CREATE INDEX idx_recipes_category ON recipes(category);")

    # Insert a sample user (username: demo, password: demo123)
    demo_password = "demo123"
    demo_hash = generate_password_hash(demo_password)
    now = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        ("demo", "demo@example.com", demo_hash, now)
    )
    demo_user_id = cur.lastrowid

    # Insert some sample recipes
    sample_recipes = [
        (
            "Masala Tea",
            "Vegetarian",
            "Water; Milk; Tea leaves; Sugar; Cardamom",
            "Boil water with cardamom, add tea leaves, add milk and sugar to taste. Simmer 2 minutes and strain.",
            "10 mins",
            None,  # no image for sample
            demo_user_id,
            now
        ),
        (
            "Simple Rice",
            "Vegetarian",
            "Rice; Water; Salt",
            "Wash rice. Add 2 cups water for 1 cup rice. Add salt. Cook until water is absorbed and rice is fluffy.",
            "20 mins",
            None,
            demo_user_id,
            now
        ),
        (
            "Aloo Tikki",
            "Snacks",
            "Potato; Salt; Red chili powder; Cumin; Oil",
            "Boil potatoes, mash, mix spices, form patties and shallow fry until golden brown.",
            "30 mins",
            None,
            demo_user_id,
            now
        )
    ]

    cur.executemany("""
        INSERT INTO recipes
        (name, category, ingredients, instructions, cooking_time, image, user_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_recipes)

    conn.commit()
    conn.close()

    print(f"✅ Database '{DB_FILE}' created successfully.")
    print("Sample user created:")
    print("  username: demo")
    print("  email: demo@example.com")
    print("  password: demo123")
    print("")
    print("You can now run your Flask app (app.py) and sign in with the demo account.")
    print("Store uploaded images under static/uploads/ (app code should save uploads there).")

if __name__ == "__main__":
    main()
