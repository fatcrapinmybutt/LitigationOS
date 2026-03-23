import sys
sys.path.insert(0, '.')
try:
    from docx_converter import convert_single, convert_directory
    print('API import OK')
    print('convert_single:', str(convert_single.__doc__)[:60] if convert_single.__doc__ else 'No doc')
    print('convert_directory:', str(convert_directory.__doc__)[:60] if convert_directory.__doc__ else 'No doc')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
