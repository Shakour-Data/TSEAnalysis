import os

root = r"c:\Users\Administrator\Documents\Analysis\TSEAnalysis"
db_path = os.path.join(root, "data", "tse_data.db")

if os.path.exists(db_path):
    size_mb = os.path.getsize(db_path) / (1024 * 1024)
    print(f"Database size: {size_mb:.2f} MB")
else:
    print("Database not found")

files_count = 0
for r, d, f in os.walk(root):
    if "venv" in r or "__pycache__" in r or ".git" in r:
        continue
    files_count += len(f)
print(f"Total files (excluding venv/pycache/git): {files_count}")
