import sys, os
import sqlite3
from datetime import datetime

# Add the system path for the generator
sys.path.append(r'C:\Users\andre\LitigationOS\00_SYSTEM\local_model')
from impeachment_generator import ImpeachmentGenerator

def main():
    gen = ImpeachmentGenerator()
    speakers = ['Tiffany Watson', 'Emily Watson', 'Judge McNeill']
    out_dir = r'C:\Users\andre\LitigationOS\05_ANALYSIS\IMPEACHMENT_PACKAGES'
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    for s in speakers:
        try:
            print(f"Processing {s}...")
            # Use the method from the class to generate the brief text
            brief = gen.generate_impeachment_brief_section(s)
            
            # Clean filename
            safe_name = s.replace(' ', '_')
            fname = f"{safe_name}_Impeachment_Brief.md"
            fpath = os.path.join(out_dir, fname)
            
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(brief)
            
            print(f"  ✅ Successfully saved: {fname}")
            
        except Exception as e:
            print(f"  ❌ Error processing {s}: {str(e)}")
            import traceback
            traceback.print_exc()

    gen.close()
    print("\nGeneration process complete.")

if __name__ == "__main__":
    main()

