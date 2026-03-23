import sys
sys.path.insert(0, '.')
try:
    from docx_templates import get_template, list_templates, MichiganCircuitTemplate, MichiganCOATemplate, MichiganDistrictTemplate
    print('Template imports OK')
    t = get_template('circuit_family')
    print('Template:', t.COURT_NAME)
    print('Case:', t.CASE_NUMBER)
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
