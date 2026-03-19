"""
Auto-categorization engine for exhibits based on file extension and name patterns.
"""

def categorize_file(filepath):
    filename = filepath.lower()
    if filename.endswith('.pdf') and 'support' in filename:
        return "Financial Evidence"
    elif filename.endswith('.docx') and 'motion' in filename:
        return "Court Motion"
    elif filename.endswith('.png') or filename.endswith('.jpg'):
        return "Photographic Evidence"
    else:
        return "Uncategorized"