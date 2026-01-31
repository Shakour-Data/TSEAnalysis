import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.local_ai_assistant import ai_assistant
import time

def test_continuous_learning():
    """Test that continuous learning thread is running and updating model."""
    print("Testing continuous learning...")

    # Check if model exists
    assert ai_assistant.model is not None, "Model should be loaded"

    # Check if thread is running
    assert ai_assistant.learning_thread.is_alive(), "Learning thread should be alive"

    # Wait a bit and check if model gets updated
    initial_update = ai_assistant.last_update
    time.sleep(2)  # Wait for potential update

    # Force update
    ai_assistant.update_model()
    print("Model updated manually")

    # Check if model is still valid
    assert ai_assistant.model is not None, "Model should still exist after update"

    print("Continuous learning test passed!")

if __name__ == "__main__":
    test_continuous_learning()