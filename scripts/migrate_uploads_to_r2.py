"""
Migrate local uploads to Cloudflare R2 and update the database.
"""
import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database
import storage

def migrate():
    load_dotenv()
    
    if not storage.is_r2_configured():
        print("Error: Cloudflare R2 is not configured in environment variables.")
        return

    conn = database.get_connection()
    
    print("Migrating material files...")
    # Materials
    materials = conn.execute("SELECT id, file_url FROM materials WHERE file_url LIKE '/static/uploads/%'").fetchall()
    for mat in materials:
        mat_id = mat["id"]
        file_url = mat["file_url"]
        local_path = os.path.join(storage.LOCAL_UPLOAD_FOLDER, os.path.basename(file_url))
        
        if os.path.exists(local_path):
            print(f"Uploading material {mat_id} ({local_path})...")
            with open(local_path, "rb") as f:
                class DummyFileStorage:
                    def __init__(self, f, name):
                        self.f = f
                        self.filename = name
                    def read(self):
                        return self.f.read()
                
                result = storage.upload_material_file(DummyFileStorage(f, os.path.basename(file_url)))
                new_url = result["file_url"]
                
                conn.execute("UPDATE materials SET file_url=? WHERE id=?", (new_url, mat_id))
                conn.commit()
                print(f"  -> Migrated to {new_url}")
        else:
            print(f"Warning: Local file not found for material {mat_id}: {local_path}")
            
    # Profile photos
    print("Migrating profile photos...")
    users = conn.execute("SELECT id, profile_photo FROM users WHERE profile_photo LIKE '/static/uploads/profile_photos/%'").fetchall()
    for u in users:
        u_id = u["id"]
        photo_url = u["profile_photo"]
        local_path = os.path.join(storage.LOCAL_UPLOAD_FOLDER, "profile_photos", os.path.basename(photo_url))
        
        if os.path.exists(local_path):
            print(f"Uploading profile photo for user {u_id}...")
            with open(local_path, "rb") as f:
                class DummyFileStorage:
                    def __init__(self, f, name):
                        self.f = f
                        self.filename = name
                    def read(self):
                        return self.f.read()
                
                new_url = storage.upload_profile_photo_file(DummyFileStorage(f, os.path.basename(photo_url)), u_id)
                conn.execute("UPDATE users SET profile_photo=? WHERE id=?", (new_url, u_id))
                conn.commit()
                print(f"  -> Migrated to {new_url}")
        else:
            print(f"Warning: Local photo not found for user {u_id}: {local_path}")
            
    conn.close()
    print("Uploads migration completed successfully!")

if __name__ == "__main__":
    migrate()
