import os
import sys

def map_fred_prime_safe(base_path):
    try:
        for root, dirs, files in os.walk(base_path):
            level = root.replace(base_path, '').count(os.sep)
            indent = '    ' * level
            try:
                print(f"{indent}{os.path.basename(root)}/")
            except Exception as e:
                print(f"{indent}[Error decoding folder name]")

            subindent = '    ' * (level + 1)
            for file in files:
                try:
                    print(f"{subindent}{file}")
                except Exception as e:
                    print(f"{subindent}[Error decoding filename]")

    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fred_path = r"F:\FRED-PRIME"
    if os.path.exists(fred_path):
        print("🔍 Mapping FRED-PRIME directory tree...\n")
        map_fred_prime_safe(fred_path)
        print("\n✅ Finished mapping FRED-PRIME.")
    else:
        print(f"❌ Directory not found: {fred_path}")
