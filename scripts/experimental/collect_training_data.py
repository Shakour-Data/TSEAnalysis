import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import db
from app.services.local_ai_assistant import LocalAIAssistant

def collect_training_data():
    """Collect training data from local database and external sources if needed."""
    print("Collecting training data...")

    # Use existing data in database
    ai = LocalAIAssistant()
    training_data = ai._collect_training_data()

    if not training_data.empty:
        print(f"Collected {len(training_data)} training samples from local database.")
        # Save to CSV for inspection
        training_data.to_csv('data/training_data.csv', index=False)
        print("Training data saved to data/training_data.csv")
    else:
        print("No training data available.")

    # For external data: In a real scenario, scrape from TSE website
    # But since we can't use external APIs, we rely on local data
    print("Note: For more data, implement scraping from TSE website (legal and local).")

if __name__ == "__main__":
    collect_training_data()
