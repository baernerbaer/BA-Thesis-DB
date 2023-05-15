import os
from appdata import AppDataPaths
from datetime import date
import sqlite3

app_paths = AppDataPaths("repetition")
db_name = "cards.db"
db = None

'''
This file handles everything regarding the database, including connection, cards, and decks.

@author David Buehler
@date January/February/March 2023
'''


def connect_DB():
    """Connects to the db. If it is empty, the schema is created without any decks or cards"""
    global db
    if db is not None:
        return
    db = sqlite3.connect(os.path.join(app_paths.app_data_path, db_name))
    db.execute("PRAGMA foreign_keys = ON;")
    print("[I] Connected to DB")
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM sqlite_master")
    if not cur.fetchone()[0]:
        print("[I] DB empty, creating schema")
        create_schema()

def close():
    global db
    if db is None:
        return
    db.close()
    db = None

def create_schema():
    """Creates the db with all necessary tables"""
    connect_DB()
    cur = db.cursor()
    cur.execute("""CREATE TABLE decks (
        name TEXT NOT NULL PRIMARY KEY,
        parent TEXT NULL, 
        FOREIGN KEY (parent) REFERENCES decks(name) ON DELETE CASCADE ON UPDATE CASCADE
    )""")
    cur.execute("""CREATE TABLE cards (
        title TEXT PRIMARY KEY,
        filename TEXT,
        created_at DATE,
        next_due_date DATE,
        last_difficulty FLOAT,
        last_interval INTEGER,
        deck TEXT NOT NULL,
        FOREIGN KEY (deck) REFERENCES decks(name) ON DELETE CASCADE ON UPDATE CASCADE
    )""")
    db.commit()
    print("[D] Schema created")

def drop_tables():
    cur = db.cursor()
    cur.execute("DROP TABLE decks")
    cur.execute("DROP TABLE cards")
    db.commit()
    print("[D] All tables were dropped")

def add_deck(name, parent=None):
    try:
        db.cursor().execute("INSERT INTO decks values (?, ?)", (name, parent))
        db.commit()
        return True
    except sqlite3.IntegrityError as e:
        print(f"Caught an Exception while trying to add deck: {e}")
        return False


def change_deck_parent(name, parent=None):
    db.cursor().execute("UPDATE decks set parent=? where name=?", (parent, name))
    db.commit()


def rename_deck(old_name, new_name):
    try:
        db.execute("UPDATE decks set name=? where name=?", (new_name, old_name))
        db.commit()
        return True
    except sqlite3.IntegrityError as e:
        print(f"Caught an Exception while trying to rename deck: {e}")
        return False
def add_card(deck, title, file=None):
    try:
        db.cursor().execute("INSERT INTO cards values (?, ?, CURRENT_DATE, CURRENT_DATE, null, null, ?)", (title, file, deck))
        db.commit()
        return True
    except sqlite3.IntegrityError as e:
        print(f"Caught an Exception while trying to add card: {e}")
        return False


def get_card(title):
    cur = db.cursor()
    cur.execute("""SELECT * from cards where title=?""", (title, ))
    return cur.fetchall()[0]


def get_cards(deck, include_children_cards=True, only_due=False):
    """Returns the cards of the deck and all of its child decks"""
    cur = db.cursor()
    if deck is None:
        if only_due:
            cur.execute("SELECT * FROM cards WHERE next_due_date <= CURRENT_DATE")
        else:
            cur.execute("SELECT * FROM cards")
    else:
        if include_children_cards:
            query = """
               WITH RECURSIVE deck_tree(name, parent) AS (
                  SELECT name, parent FROM decks WHERE name = ?              
                  UNION ALL
                  -- Recursive step: add child decks to the result set
                  SELECT d.name, d.parent
                  FROM decks d
                  JOIN deck_tree dt ON dt.name = d.parent
                ) 
                
                SELECT c.*
                FROM cards AS c
                JOIN deck_tree AS dt ON c.deck = dt.name
            """
        else:
            query = "SELECT * from cards where deck = ?"

        if only_due:
            query += "WHERE next_due_date <= CURRENT_DATE\n"
        cur.execute(query, (deck, ))
    return cur.fetchall()


def update_card_after_review(title, difficulty, stability, next_due_date):
    if next_due_date is date:
        next_due_date = next_due_date.strftime('%Y-%m-%d')
    cur = db.cursor()
    cur.execute("UPDATE cards set last_difficulty = ?, last_interval = ?, next_due_date = ? WHERE title=?", (difficulty, stability, next_due_date, title))
    db.commit()


def rename_card(old_title, new_title):
    try:
        db.cursor().execute("UPDATE cards set title=? where title=?", (new_title, old_title))
        db.commit()
        return True
    except sqlite3.IntegrityError as e:
        print(f"Caught an Exception while trying to rename card: {e}")
        return False


def delete_card(title):
    file_name = db.execute("SELECT filename FROM cards WHERE title=?", (title, )).fetchall()[0][0]
    os.remove(os.path.join(app_paths.app_data_path, file_name))
    db.execute("DELETE FROM cards WHERE title=?", (title, ))
    db.commit()

def get_decks():
    cur = db.cursor()
    cur.execute("""SELECT * from decks""")
    return cur.fetchall()


def delete_deck(deck):
    cur = db.cursor()
    for card in get_cards(deck, include_children_cards=True, only_due=False):
        if card["filename"]:
            os.remove(os.path.join(app_paths.app_data_path, card["filename"]))
    cur.execute("""DELETE FROM decks WHERE name=?""", (deck, ))
    db.commit()

