"""
Migrate data from local SQLite database to Supabase PostgreSQL.
"""
import os
import sqlite3
import psycopg2
import psycopg2.extras
import sys

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database

def migrate():
    load_dotenv()
    
    pg_url = os.environ.get("DATABASE_URL")
    if not pg_url:
        print("Error: DATABASE_URL not found in environment.")
        return

    db_path = database.DATABASE_PATH
    if not os.path.exists(db_path):
        print(f"Error: Local SQLite database not found at {db_path}")
        return
        
    print("Connecting to PostgreSQL...")
    pg_conn = psycopg2.connect(pg_url)
    pg_cursor = pg_conn.cursor()

    print("Connecting to SQLite...")
    sl_conn = sqlite3.connect(db_path)
    sl_conn.row_factory = sqlite3.Row
    sl_cursor = sl_conn.cursor()

    tables = ["users", "materials", "reviews", "bookmarks", "material_upvotes", "contributors"]

    try:
        print("Initializing PostgreSQL schema...")
        database.init_db() # This will ensure schema exists
        
        for table in tables:
            print(f"Migrating table: {table}...")
            sl_cursor.execute(f"SELECT * FROM {table}")
            rows = sl_cursor.fetchall()
            if not rows:
                print(f"  No rows to migrate for {table}.")
                continue
                
            cols = rows[0].keys()
            col_str = ", ".join(cols)
            val_str = ", ".join(["%s"] * len(cols))
            
            pg_cursor.execute(f"TRUNCATE {table} RESTART IDENTITY CASCADE;")
            
            insert_query = f"INSERT INTO {table} ({col_str}) VALUES ({val_str})"
            data_to_insert = [tuple(row) for row in rows]
            
            psycopg2.extras.execute_batch(pg_cursor, insert_query, data_to_insert)
            print(f"  Migrated {len(rows)} rows for {table}.")
            
        pg_conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        pg_conn.rollback()
        print(f"Error during migration: {e}")
        
    finally:
        pg_cursor.close()
        pg_conn.close()
        sl_cursor.close()
        sl_conn.close()

if __name__ == "__main__":
    migrate()
