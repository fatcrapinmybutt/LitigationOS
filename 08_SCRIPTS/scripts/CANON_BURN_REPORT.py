
def generate_canon_report(judicial_violations):
    return "\n".join([f"Canon Violation: {v}" for v in judicial_violations])

if __name__ == "__main__":
    violations = ["Canon 1: Failing to uphold independence", "Canon 3: Bias during PPO hearing"]
    print(generate_canon_report(violations))
