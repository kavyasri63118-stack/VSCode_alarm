import os
import sys
import time

# Ensure parent directory is in sys.path for direct running
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from code_alarm import notify

@notify("Heavy Data Processing")
def process_data():
    print("⏳ Starting data processing...")
    for i in range(5):
        print(f"  • Processing batch {i+1}/5...")
        time.sleep(0.5)
    print("✨ Finished batch processing!")
    return True

if __name__ == "__main__":
    process_data()
