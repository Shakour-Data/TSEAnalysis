import subprocess
import sys
import os

def run_coverage_tests():
    print("Running Utils Coverage Tests...")

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_utils_coverage.py",
        "tests/test_utils_extra_coverage.py",
        "tests/test_nan_handler_extra.py",
        "tests/test_validators_extra.py",
        "tests/test_duplicate_handler_extra.py",
        "tests/test_chart_optimizer_extra.py",
        "tests/test_encoding_utils_remaining.py",
        "tests/test_nan_handler_remaining.py",
        "tests/test_validators_remaining.py",
        "tests/test_chart_optimizer_remaining.py",
        "--cov=app/utils",
        "--cov-report=term-missing",
        "--cov-report=html:cov_html"
    ]

    try:
        result = subprocess.run(cmd, cwd=os.getcwd())
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = run_coverage_tests()
    if success:
        print("Tests completed successfully!")
    else:
        print("Tests failed!")