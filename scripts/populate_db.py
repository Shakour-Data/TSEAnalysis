
from app import TSETMCClient, API_KEY
import json

client = TSETMCClient(API_KEY)

print("Populating Symbols Registry...")
# Fetch main markets to populate DB
client.get_all_symbols("1", force_refresh=True)
client.get_all_symbols("2", force_refresh=True)
client.get_all_symbols("3", force_refresh=True)
print("Registry Populated.")
