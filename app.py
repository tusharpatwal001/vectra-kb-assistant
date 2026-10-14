from src.assistant import answer

SAMPLES = [
    "My account got locked. How long until it unlocks by itself?",
    "What VPN server address should I use when working from home?",
    "What is the resolution target for a P2 ticket?",
    "How do I get a parking pass for the Gurugram office?",
    "Hi, I'm Anand Sharma (anand.sharma@vectralogistics.example, +91 9876543210). Company mail doesn't show up in my iPhone's built-in Mail app.",
]

if __name__ == "__main__":
    for q in SAMPLES:
        print(f"Q: {q}")
        print(f"A: {answer(q)}\n{'-'*60}")