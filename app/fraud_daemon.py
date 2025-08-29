import time
from app.fraud_model import run_model

def main():
    print("Fraud scoring loop. Ctrl+C to stop.")
    while True:
        flagged = run_model()
        if flagged:
            print(f"Alert: {flagged} new suspicious transactions.")
        time.sleep(10)  # poll every 10s (local demo)

if __name__ == "__main__":
    main()
