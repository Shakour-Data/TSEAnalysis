
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.tsetmc import client
import json

print("Populating Symbols Registry...")
# Fetch main markets to populate DB
client.get_all_symbols("1", force_refresh=True)
client.get_all_symbols("2", force_refresh=True)
client.get_all_symbols("3", force_refresh=True)
print("Registry Populated.")
