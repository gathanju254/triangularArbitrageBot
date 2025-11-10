import os
import shutil
from pathlib import Path

print("🔄 Starting fresh database setup...")

# Delete database if exists
db_path = Path("db.sqlite3")
if db_path.exists():
    db_path.unlink()
    print("✅ Deleted old database")

# Run migrations
print("🔄 Applying migrations...")
os.system("python manage.py migrate")

print("🎉 Fresh start completed!")