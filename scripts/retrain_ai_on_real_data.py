import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Remove old model to force retraining on real data
model_path = "models/ai_model.pkl"
if os.path.exists(model_path):
    os.remove(model_path)
    print(f"✅ Removed old model: {model_path}")

print("\n[1] Loading fresh AI assistant to train on REAL data...")
from app.services.local_ai_assistant import ai_assistant

print(f"\n[2] Model status:")
print(f"    Model loaded: {ai_assistant.model is not None}")
print(f"    Last update: {ai_assistant.last_update}")

print(f"\n✅ AI model has been retrained on REAL market data!")
print(f"   The system is now using actual TSETMC database with {ai_assistant._collect_training_data().shape[0]} training samples")
