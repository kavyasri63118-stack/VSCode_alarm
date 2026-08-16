import os
import sys
import time

# Ensure parent directory is in sys.path for direct running
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from code_alarm import CodeAlarm

def run_simulation():
    with CodeAlarm("Physics Simulation"):
        print("🚀 Running physics simulation...")
        time.sleep(2)
        print("📊 Computing matrix transformations...")
        time.sleep(1)
        print("🎯 Simulation calculation converged!")

if __name__ == "__main__":
    run_simulation()
