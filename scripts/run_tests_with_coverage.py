import subprocess
import sys
import os

def run_tests():
    print("🚀 Starting Backend Test Suite with Coverage...")
    
    # Run pytest with coverage on the whole tests directory
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html:docs/reports/coverage"
    ]
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    try:
        result = subprocess.run(cmd, env=env)
        if result.returncode == 0:
            print("\n✅ All Backend Tests Passed!")
        else:
            print("\n❌ Some Backend Tests Failed.")
            
        print("\n📊 Coverage report generated in docs/reports/coverage/index.html")
    except Exception as e:
        print(f"Error running tests: {e}")

if __name__ == "__main__":
    run_tests()
