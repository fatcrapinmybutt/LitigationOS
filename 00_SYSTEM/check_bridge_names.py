"""Check actual bridge naming in v7 HTML."""
text = open(r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v7\THEMANBEARPIG_v7.html", encoding="utf-8").read()

# Find the bridge section
bridge_start = text.find('FULL CONVERGENCE')
if bridge_start == -1:
    bridge_start = text.find('pywebview')
    
# Check actual namespaces used
for term in ['MBP.', 'Backend', 'Palette', 'Results', 'StatusBar', 
             'command-palette', 'mbpBackend', 'mbpPalette', 'mbpResults',
             'mbp-cmd', 'cmdPalette', 'cmd-palette']:
    count = text.count(term)
    if count > 0:
        print(f"  '{term}': {count} occurrences")

# Find the bridge injection point
idx = text.rfind('</body>')
if idx > 0:
    # Show 200 chars before </body>
    snippet = text[idx-200:idx+10]
    # Print safely
    safe = snippet.encode('ascii', 'replace').decode('ascii')
    print(f"\nBefore </body> (last 200 chars):")
    print(safe)

# Also check if injection went in at all
print(f"\n'window.pywebview' count: {text.count('window.pywebview')}")
print(f"'CONVERGENCE' count: {text.count('CONVERGENCE')}")
print(f"'Ctrl+K' count: {text.count('Ctrl+K')}")
print(f"'MBP.call' count: {text.count('MBP.call')}")
print(f"Total size: {len(text):,} chars")

# Check the injection script exists
import os
conv_script = r"D:\LitigationOS_tmp\selfevolve_exe_convergence.py"
if os.path.exists(conv_script):
    print(f"\nConvergence script exists: {os.path.getsize(conv_script):,} bytes")
else:
    print("\nWARNING: Convergence script NOT FOUND")
