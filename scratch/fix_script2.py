from pathlib import Path
p=Path('scratch/edit_report.py'); s=p.read_text(encoding='utf-8-sig')
s=s.replace("for p in doc.paragraphs:\n if doc.paragraphs.index(p) < 37: continue", "for qi,p in enumerate(doc.paragraphs):\n if qi < 37: continue")
p.write_text(s,encoding='utf-8')
