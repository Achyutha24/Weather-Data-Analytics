# Template contract for the Weather Data Analytics report

## Reference and fidelity authority

- Reference DOCX: `C:\Users\achyu\Downloads\cc report task 1.docx`.
- SHA-256 at inspection: `2625f0aacb7cf6ff2dee5cc1dc919370c5601cc6996a87fc7a843549af90f4b6`.
- Word rendering: `scratch/source-current-review.pdf`, 19 pages. Pages 1–18 contain the report; page 19 is blank.
- Visual render pages: `scratch/source-current-render/page-*.png`; 5-column contact sheet: `scratch/source-current-render/contact.png`.
- Companion PDF in `reference/` is an older-content visual aid with different cover details. The current DOCX is the authority for administrative details and template structure.
- Package structure: 12 sections, A4 portrait (8.27 × 11.69 in), 349 body paragraphs, no native Word tables, 46 body drawings plus recurring header/footer artwork. Part sizes and hashes are in `scratch/source-package-inventory.csv`.

## Page system and recurring components

- Cover: full-page black border; centered institutional title and seal; college banner and original administrative block. Preserve all original identity and academic-year text exactly as currently shown in the DOCX: Achyutha Sai V (1VE23CA002), Mrs. Vimala Devi R, SVCE/VTU institutional text, 2025–2026.
- Abstract and table of contents: separate front-matter pages without the body running header/footer. Preserve the source heading and paragraph styles.
- Main body: A4 portrait. Source body sections use 0.79 in left/right margins; retain section-specific margins and header/footer distances, except adjust only breaks that create a blank final page or an empty page after removed legacy screenshots.
- Main body running header: centered short weather project title, academic year at right, and thin brown rule. Footer: department/institution text, brown rule, and automatic page field. Preserve header/footer parts and their relationship/linking structure.
- Cover and front matter have different section/header behavior from the body. Keep the source's section count and header/footer parts; use continuous section starts only where needed to remove empty transitions.

## Typography, lists, and page density

- Reuse source paragraph styles, direct formatting, and numbering definitions. Body text is justified serif text; chapter headings are bold and numbered, subheadings use the source's bold numbered subsection treatment, and table-of-contents entries use the source TOC style.
- Do not shrink body text to force pagination. The two requirements-introduction paragraphs are anomalously styled as Heading 3 in the source; convert these two paragraphs to the regular body style so prose does not render as oversized headings.
- Keep the original centered cover arrangement and logo positions. Add the second line of the new project title by cloning the existing title paragraph formatting.
- Remove empty body spacers left by obsolete screenshots and the trailing section break responsible for page 19. Keep the cover/front-matter spacing and section boundaries.

## Content slots and allowed changes

- Cover: change only the project title; retain all institutional/student/guide/year details.
- Abstract: replace four body paragraphs with the implemented objective, ingestion, storage, analytics, dashboard, test/sample evidence, and data-verification limitation.
- TOC: preserve six chapter entries and update the visible page references after final Word pagination.
- Chapters 1–6: replace old virtualization content throughout. Keep the source chapter heading/list presentation. Insert editable requirement, configuration, architecture, and evidence tables using source-derived borders and restrained brown accents.
- Legacy screenshots/diagrams: remove all VM, Ubuntu, VirtualBox and unrelated generated imagery. Retain the two cover logos. Use an editable Word architecture flow table because no weather dashboard or Compass screenshots are present in the project files.
- Results: distinguish verified repository/test/sample evidence from dashboard values reported in the task brief; do not present live database metrics as independently verified without a reachable database snapshot.

## Package preservation and fidelity gates

- Preserve source document sections, page geometry, cover artwork, logos, header/footer text boxes, border/rule artwork, styles, numbering, PAGE fields, and institutional details.
- Keep the source DOCX untouched. Final output must be a separate file at `C:\Users\achyu\Desktop\BDA\output\Weather_Data_Storage_and_Analysis_MongoDB_Report.docx`.
- After editing, compare every rendered page with the source pattern at 100% zoom; verify no blank pages, missing page rules, clipped tables, stale screenshots, stale text, or orphaned body images.
- Refresh Word fields, update TOC page references from final pagination, and check the source SHA-256 again before delivery.
