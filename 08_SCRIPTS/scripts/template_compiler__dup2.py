import os
from jinja2 import Template
from docx import Document

def render_text_template(text_template:str, context:dict)->str:
    return Template(text_template).render(**(context or {}))

def render_docx_from_text(text_template:str, context:dict, out_path:str):
    rendered = render_text_template(text_template, context)
    doc = Document()
    for line in rendered.splitlines():
        doc.add_paragraph(line)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc.save(out_path)
    return out_path
