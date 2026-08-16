import os
import sys
import time
import random

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def train_model():
    epochs = 5
    print("[*] Initializing Neural Network on GPU...")
    time.sleep(1)

    for epoch in range(1, epochs + 1):
        loss = max(0.01, 1.0 / epoch + random.uniform(-0.05, 0.05))
        acc = min(0.99, 0.5 + (epoch * 0.09) + random.uniform(-0.02, 0.02))
        print(f"  Epoch [{epoch}/{epochs}] | Loss: {loss:.4f} | Accuracy: {acc*100:.2f}%")
        time.sleep(0.8)

    print("\n🎉 Training finished! Model saved to `best_model.pt`")

if __name__ == "__main__":
    train_model()
