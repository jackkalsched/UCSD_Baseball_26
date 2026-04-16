import sys
from pathlib import Path

# Resolve the project root dynamically to safely access project components
# `experimental/scratchpads/template_test.py` -> parents[2] resolves to `UCSD_Baseball_26` root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# Example: Using the suite from your testing sandbox!
# from analytics_suite.run_expectancy import generate_base_out_state

def test_sandbox():
    print("Welcome to your isolated experimental workspace.")
    print(f"Project root correctly resolved to: {PROJECT_ROOT}")
    
    # test your custom data or dummy models here...
    # model = joblib.load(Path(__file__).resolve().parent / "test_model.pkl")

if __name__ == "__main__":
    test_sandbox()
