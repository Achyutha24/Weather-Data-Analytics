from pathlib import Path
p=Path('scratch/edit_report.py'); s=p.read_text(encoding='utf-8-sig')
s=s.replace('for p in list(doc.paragraphs):\n if p.text.strip(): continue', 'for pi,p in enumerate(list(doc.paragraphs)):\n if p.text.strip(): continue')
s=s.replace(' bodyparas=doc.paragraphs\n if bodyparas.index(p) < 37: continue', ' if pi < 37: continue')
p.write_text(s,encoding='utf-8')
