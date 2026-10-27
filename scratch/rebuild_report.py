from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from copy import deepcopy
from pathlib import Path
from lxml import etree
import zipfile, shutil, re

path=Path('output/Weather_Data_Storage_and_Analysis_MongoDB_Report_Final_Reviewed.docx')
source=Path(r'C:\Users\achyu\Downloads\cc report task 1.docx')
shutil.copy2(source,path)
doc=Document(path)
P={i:p for i,p in enumerate(doc.paragraphs)}
# Replace text nodes in place so Word drawings, section properties, run formatting, and page furniture survive.
def set_paragraph_text(p,text):
 nodes=[]
 for run in p._p.findall(qn('w:r')):
  if run.find(qn('w:drawing')) is not None or run.find(qn('w:pict')) is not None:
   continue
  nodes.extend(run.findall(qn('w:t')))
 if not nodes:
  run=OxmlElement('w:r'); node=OxmlElement('w:t'); run.append(node); p._p.append(run); nodes=[node]
 nodes[0].text=text
 if text[:1].isspace() or text[-1:].isspace(): nodes[0].set('{http://www.w3.org/XML/1998/namespace}space','preserve')
 else: nodes[0].attrib.pop('{http://www.w3.org/XML/1998/namespace}space',None)
 for node in nodes[1:]: node.text=''
def current_index(i):
 # The supplied DOCX has one fewer cover-title paragraph than the earlier draft.
 return i if i <= 5 else i-1
def put(i,text):
 set_paragraph_text(P[current_index(i)],text)

# Preserve cover administration and university/college artwork; replace only the title.
put(5,'WEATHER DATA STORAGE AND ANALYSIS')
# Add the second title line as a clone of the source title paragraph, preserving its formatting.
title2_xml=deepcopy(P[5]._p)
P[5]._p.addnext(title2_xml)
title2=Paragraph(title2_xml,P[5]._parent)
set_paragraph_text(title2,'USING MONGODB FOR BIG DATA PROCESSING')
# Abstract
put(21,'Weather observations are generated continuously and are useful for studying temperature, rainfall, humidity, wind, and seasonal patterns. This project develops a Python-based workflow for collecting historical observations, validating them, and storing them in a local MongoDB Community Server database. It is designed to provide a structured, repeatable way to query weather records from multiple Indian cities.')
put(22,'The implementation supports hourly historical data retrieval from the Open-Meteo Historical Weather API and incremental import of compatible CSV files. Pandas reads CSV data in chunks, while normalization routines parse timestamps, sanitize meteorological values, reject invalid records, and map accepted rows to a common document schema. PyMongo performs unordered bulk upserts into MongoDB collections, with indexes to support filtering and prevent duplicate logical observations.')
put(23,'MongoDB aggregation pipelines calculate summaries and trends without first loading the full collection into a Python data frame. A Streamlit dashboard presents these results through Plotly charts and provides city and date filters, data exploration, ingestion controls, database diagnostics, and CSV export. MongoDB Community Server is the storage and query engine; MongoDB Compass is an optional graphical client for inspecting it.')
put(24,'The supplied project contains automated tests for data validation, API response parsing, CSV handling, database upsert logic, aggregation behavior, and application imports. All 19 tests passed during this review. The supplied sample CSV contains five hourly Bengaluru observations. Live database totals and the previously reported dashboard figures could not be independently confirmed because the MongoDB service was inaccessible in this environment.')
# Contents entries, keep the source's six-section arrangement.
put(29,'INTRODUCTION ........................................................ 1')
put(30,'SYSTEM REQUIREMENTS AND SPECIFICATIONS ............................. 3')
put(31,'SYSTEM DESIGN ..................................................... 4')
put(32,'IMPLEMENTATION .................................................... 5')
put(33,'RESULT ............................................................ 8')
put(34,'CONCLUSION ....................................................... 10')
# Use the source TOC paragraphs' right-aligned dotted tab stops instead of typed dot strings.
for idx,title,page in [
 (29,'INTRODUCTION','1'),
 (30,'SYSTEM REQUIREMENTS AND SPECIFICATIONS','3'),
 (31,'SYSTEM DESIGN','4'),
 (32,'IMPLEMENTATION','5'),
 (33,'RESULT','8'),
 (34,'CONCLUSION','10')]:
 para=P[current_index(idx)]
 for run in list(para.runs):
  para._p.remove(run._r)
 run=para.add_run(title); run.add_tab(); para.add_run(page)
# Introduction
put(39,'INTRODUCTION')
put(41,'Weather conditions affect transport, agriculture, water management, public health, and everyday planning. Historical observations help analysts compare conditions across locations and time periods. When records are stored in separate files or examined manually, it becomes difficult to maintain consistent formats, prevent duplicates, and answer questions across large date ranges.')
put(42,'This project addresses those needs with a local document database and a Python analytics application. MongoDB stores each observation as a flexible document containing location, timestamp, granularity, source, and meteorological measurements. This structure supports records from the historical API and compatible CSV datasets while allowing analytical queries to filter and group the documents.')
put(43,'The system uses Python for orchestration and validation, PyMongo for database access, Pandas for chunked CSV processing, and Streamlit with Plotly for interactive presentation. The data source implemented for historical retrieval is the Open-Meteo Archive API. The code also includes a registry of ten Indian cities. The project is intended as an educational analytics system and does not issue forecasts or safety alerts.')
put(44,'Problem Statement: A practical way is needed to collect and organize historical weather observations from different sources, validate their fields, store them with duplicate protection, and produce useful summaries without manually processing the full dataset for every query.')
put(48,'Project Scope: The implementation covers hourly API retrieval, CSV ingestion, canonical record validation, local MongoDB storage, compound indexes, aggregation-based analytics, and a Streamlit dashboard. The API fetcher divides long date ranges into bounded requests. CSV processing reads chunks to limit memory use. Both ingestion paths share the same record schema and database upsert layer.')
put(49,'The project focuses on historical data analysis rather than real-time sensor acquisition or weather forecasting. Open-Meteo provides archived weather series; compatible CSV data can also be imported when its fields can be mapped to the supported schema. MongoDB Compass may be used to browse the database, but it is not required to run the Python application and does not replace the MongoDB server.')
put(50,'The system is useful because it keeps data ingestion, storage, analysis, and presentation in one reproducible workflow. A consistent schema simplifies city and date filters. Server-side aggregation allows the database to perform grouping and summary calculations. The dashboard gives users a visual interface for exploring the results and exporting filtered records.')
put(51,'The objectives are to acquire historical observations from supported sources; validate timestamps and meteorological values; store records in MongoDB with indexes and idempotent upserts; compute temperature, precipitation, humidity, wind, extremes, and data-completeness summaries; and present interactive charts and filtered records in a dashboard.')
put(52,'The expected benefit is an extensible foundation for comparative weather analysis. It demonstrates how a document database can support mixed-source time-series records and how database aggregation can reduce unnecessary transfer of raw records into the application. The reported results in this document distinguish tested code and supplied sample data from figures that could not be checked against a live database.')
# Requirements
put(85,'SYSTEM REQUIREMENTS AND SPECIFICATIONS')
put(87,'The application runs on a Windows development computer and connects to a local MongoDB Community Server. Hardware guidance below is a practical recommendation for running the database, Python environment, and interactive dashboard together; it is not a measured configuration of the project computer.')
put(88,'MongoDB Compass is optional and serves as a graphical database client. The required database service is MongoDB Community Server. Python package versions are managed through requirements.txt; the project does not pin exact versions.')
put(121,'By default, the application connects to mongodb://127.0.0.1:27017/ and uses the weather_analytics database. Environment variables can override the URI, database, timeout, and batch size. db.py creates collections and indexes when the application connects.')
# System Design
put(124,'SYSTEM DESIGN')
put(125,'The design separates ingestion, validation, persistence, analytics, and presentation. Historical API requests are made by the fetcher; CSV uploads are handled by the importer. Both paths normalize records before calling the shared PyMongo bulk-upsert layer.')
put(126,'The canonical weather_observations collection stores individual observations. The ingestion_runs collection records run metadata and processing counts. The MongoDB server executes aggregation pipelines for summaries, city comparisons, time trends, precipitation, extremes, data quality, and bounded relationship samples. The Streamlit application converts returned results into tables and Plotly visualizations.')
put(127,'The main components and data flow are:')
put(128,'Historical Open-Meteo Archive API')
put(129,'Compatible CSV file, processed in chunks with Pandas')
put(130,'Python validation and normalization')
put(131,'PyMongo batch upserts to local MongoDB Community Server')
put(132,'MongoDB collections, indexes, and aggregation pipelines')
put(133,'Python analytics functions and Streamlit interface')
put(135,'Plotly charts, filtered records, diagnostics, and CSV export')
put(136,'The architecture provides the following behavior:')
put(137,'A common schema maps multiple sources to the same fields.')
put(138,'Timestamp and numeric checks reject malformed or out-of-range values.')
put(139,'Compound unique keys support repeatable upserts for a city, timestamp, granularity, and source.')
put(140,'MongoDB performs grouping and summary work close to stored data.')
put(141,'The dashboard applies city, date, granularity, and source filters where available.')
put(142,'Compass is available for manual inspection but is not part of the storage execution path.')
put(143,'') # Detailed index definitions are presented in the implementation chapter.
put(144,'')
# Implementation: detailed descriptions in existing paragraph slots
put(148,'IMPLEMENTATION')
put(149,'The project is implemented as a set of Python modules. config.py contains environment-driven MongoDB settings, the Open-Meteo endpoint, supported API variables, and the Indian city registry. weather_fetcher.py retrieves and parses API responses. weather_utils.py validates and normalizes records. import_data.py handles CSV input. db.py manages MongoDB connections, indexes, bulk upserts, and ingestion-run records. analytics.py defines aggregation queries, and app.py provides the Streamlit dashboard.')
put(150,'The software dependencies listed in requirements.txt include PyMongo, Pandas, Streamlit, Plotly, Requests, python-dotenv, Pytest, and mongomock. MongoDB Community Server must be installed and running locally for database operations. Compass can be installed separately when visual inspection is desired.')
put(152,'4.1 Environment and Configuration')
put(153,'The application reads MONGODB_URI, MONGODB_DATABASE, MONGODB_CONNECT_TIMEOUT_MS, and MONGODB_BATCH_SIZE from the environment, with defaults in config.py. The default URI is local loopback port 27017 and the default database is weather_analytics. A connection check is implemented in check_connection.py.')
put(154,'Configuration steps:')
put(155,'Install Python and the packages listed in requirements.txt.')
put(156,'Install MongoDB Community Server and start its service.')
put(157,'Optionally install MongoDB Compass as a client for inspecting records.')
put(158,'Set environment variables when the default URI or database should be changed.')
put(159,'Run the application scripts from the project directory.')
put(160,'The repository README documents a virtual environment setup and dashboard launch command.')
put(162,'4.2 Historical API Ingestion')
put(163,'weather_fetcher.py requests hourly variables from the Open-Meteo Historical Archive endpoint. The implementation maps temperature, relative humidity, precipitation, wind speed and direction, surface pressure, cloud cover, and weather code into canonical field names.')
put(164,'API processing workflow:')
put(165,'Select registered cities and a valid inclusive start and end date.')
put(166,'Split long date ranges into bounded chunks.')
put(167,'Request each chunk and parse the returned hourly arrays.')
put(168,'Normalize observations with location, timezone, source, and granularity metadata.')
put(169,'Record run status and accepted, rejected, inserted, or updated counts when the database operation completes.')
put(172,'4.3 CSV Ingestion and Data Validation')
put(173,'import_data.py reads CSV files with Pandas chunks, maps recognized column names to the common schema, and allows a default city where the file does not provide one. It supports a dry-run option for validation without database writes. The supplied sample_weather.csv contains five rows for Bengaluru, dated 1 January 2023 from 00:00 through 04:00.')
put(174,'Validation and normalization include:')
put(175,'Parse supported timestamp representations and normalize timestamps to UTC-aware values.')
put(176,'Require a city and valid timestamp; reject records that fail required-field checks.')
put(177,'Sanitize numeric meteorological values against bounds defined in weather_utils.py.')
put(178,'Normalize the granularity to hourly or daily and assign a source label.')
put(179,'Preserve missing measurements as null values instead of converting them to zero.')
put(180,'Process rows incrementally so a large input file need not be loaded as one data frame.')
put(181,'The importer reports read, accepted, rejected, inserted, and updated record counts.')
put(182,'The example CSV is a small fixture and should not be interpreted as the full dashboard dataset.')
put(184,'4.4 MongoDB Schema and Indexes')
put(185,'The weather_analytics database uses two collections. weather_observations stores one normalized weather observation per document. ingestion_runs stores source, requested locations and date range, run times, status, and processing counts.')
put(186,'Observation fields include:')
put(187,'city, country, latitude, longitude, timezone, timestamp, granularity, and source.')
put(188,'temperature_c, relative_humidity_pct, precipitation_mm, wind_speed_kmh, and wind_direction_deg.')
put(189,'pressure_msl_hpa, cloud_cover_pct, weather_code, and ingested_at.')
put(190,'A compound unique index on city, timestamp, granularity, and source supports idempotent upserts.')
put(191,'Additional timestamp, city/timestamp, and granularity indexes support common filters.')
put(192,'The separate ingestion_runs collection provides an audit history of import activity.')
put(194,'4.5 Bulk Write and Duplicate Prevention')
put(195,'db.py converts normalized documents into unordered bulk update operations. Each operation matches the compound logical key and uses upsert behavior. Re-ingesting the same source record therefore updates the matching document instead of intentionally adding a second copy. The unique index enforces the same key at the database level.')
put(196,'The ingestion workflow:')
put(197,'Prepare a bounded batch of validated documents.')
put(198,'Build a filter from city, timestamp, granularity, and source.')
put(199,'Submit unordered bulk operations through PyMongo.')
put(200,'Collect inserted and updated counts from the bulk result.')
put(201,'Handle bulk write and connection errors through the database layer.')
put(204,'Write or update an ingestion run record with the final status and counts.')
put(205,'Refresh dashboard data after a successful interactive ingestion.')
put(206,'Use the unique index to reject duplicate logical observations.')
put(207,'The implementation is designed for repeatable imports and bounded batch processing.')
put(209,'4.6 Aggregation and Analytics')
put(210,'analytics.py builds MongoDB aggregation pipelines for database summaries and analytical views. The queries filter records, group by city or time period, project derived values, and sort results before returning bounded data to the dashboard.')
put(211,'Implemented analyses include:')
put(212,'Counts, date coverage, temperature extrema, averages, and precipitation totals.')
put(213,'Temperature summaries by city and daily or monthly temperature trends.')
put(214,'Annual comparisons, monthly rainfall trends, and wettest dates.')
put(215,'Humidity summaries, weather-code distributions, and high-wind records.')
put(216,'Data-quality completeness and null-field summaries.')
put(217,'A bounded sample for variable relationships and Pearson correlation displays.')
put(219,'4.7 Dashboard and Data Export')
put(220,'The Streamlit application provides eight navigation areas: overview; temperature trends; multi-city comparison; precipitation; wind and extremes; variable relationships; data explorer; and database diagnostics and ingestion. Plotly charts visualize returned aggregates. Filters select cities and date ranges, and the data explorer supports paginated database queries and CSV export.')
# The preceding paragraph already summarizes all eight dashboard areas; remove the repeated list.
for idx in range(220,227):
 set_paragraph_text(P[idx],'')
# Results
put(237,'5. RESULT')
put(238,'The source code and supplied data demonstrate a complete implementation path from historical API or CSV input to MongoDB storage, aggregation, and dashboard presentation. The test suite completed with 19 passing tests during this review. These tests cover representative logic paths with mocked responses and in-memory database fixtures; they do not prove that an external API request or a live MongoDB deployment succeeded during this review.')
put(239,'The supplied sample CSV has five valid-looking hourly rows for Bengaluru on 1 January 2023. It includes temperature, humidity, precipitation, wind, pressure, cloud cover, and weather-code columns. The test suite includes a separate importer fixture that checks accepted and rejected rows in dry-run mode.')
put(240,'The application code contains dashboard views for temperature, precipitation, city comparison, wind events, extremes, relationships, data exploration, and database diagnostics. The configured Open-Meteo fetcher supports ten registered Indian cities. These are implemented capabilities visible in source code, not independently confirmed live data results.')
put(241,'A previous dashboard view was reported to display 26,280 observations, a mean temperature of 24.89 °C, cumulative precipitation of 3,704.1 mm, a January-to-December 2023 coverage interval, and Bengaluru, Delhi, and Mumbai. The MongoDB service was not reachable from this environment, and no dashboard capture was available for inspection; these figures are therefore recorded as previously reported dashboard values, not verified database measurements.')
put(242,'No processing-speed benchmark or live collection size is claimed. The five-row CSV fixture is not representative of the 26,280 observations mentioned above. MongoDB Compass screenshots and weather dashboard screenshots were not available in the supplied project files, so the legacy installation screenshots were removed and the system architecture figure was replaced with a project-specific diagram.')
put(246,'Table 5.1 summarizes the evidence confirmed from the supplied project files and separates it from values reported in the task brief.')
put(247,'The system is suitable as a demonstrator for historical data ingestion and analytics. Its practical value depends on source-data quality, database availability, and the chosen date range. Interpretations of correlations remain exploratory and should not be used as causal conclusions or weather forecasts.')
# Conclusion
put(343,'6. CONCLUSION')
put(344,'This project implements a local weather data storage and analytics workflow using Python and MongoDB. It provides historical API retrieval, chunked CSV import, normalization and validation, PyMongo bulk upserts, MongoDB indexes and aggregation pipelines, and a Streamlit and Plotly dashboard for interactive analysis.')
put(345,'The system stores observations separately from ingestion-run metadata and uses a compound unique key to support duplicate-resistant imports. The analytics layer includes city and time-period summaries, rainfall and wind analysis, extremes, data completeness, and bounded variable relationships. The dashboard also provides filtered record exploration and CSV export.')
put(346,'During this review, all 19 automated tests passed and the supplied CSV was confirmed to contain five Bengaluru hourly records. The MongoDB service could not be accessed from this environment, so collection counts and earlier dashboard metrics remain unverified. The report treats those earlier figures as reported dashboard values rather than measured database results.')
put(347,'Possible future improvements include validating a full production-sized dataset, adding reproducible ingestion logs, documenting a live deployment and database backup procedure, and extending the dashboard with carefully sourced comparisons. Any future performance claims should be based on recorded benchmark conditions and repeatable measurements.')
put(348,'The implementation demonstrates how a document database and server-side aggregation can organize historical weather observations for interactive analysis, while preserving a clear distinction between implemented features, tested behavior, and results that require live data verification.')

# These two source paragraphs were incorrectly assigned Heading 3; use the source body style.
for idx in (86,87):
 P[idx].style=doc.styles['Normal']
 P[idx].alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
 P[idx].paragraph_format.space_after=Pt(6)

# Keep the results chapter visually aligned with the other chapter starts.
result_heading=P[236]
if result_heading._p.pPr is None:
 result_heading._p.insert(0,OxmlElement('w:pPr'))
if result_heading._p.pPr.find(qn('w:pageBreakBefore')) is None:
 result_heading._p.pPr.append(OxmlElement('w:pageBreakBefore'))

# Clear any old prose not in explicitly replaced slots, keeping layout paragraphs and breaks.
used=set([5,6,21,22,23,24,29,30,31,32,33,34,39,41,42,43,44,48,49,50,51,52,85,87,88,121,124,125,126,127,128,129,130,131,132,133,135,136,137,138,139,140,141,142,143,144,148,149,150,152,153,154,155,156,157,158,159,160,162,163,164,165,166,167,168,169,172,173,174,175,176,177,178,179,180,181,182,184,185,186,187,188,189,190,191,192,194,195,196,197,198,199,200,201,204,205,206,207,209,210,211,212,213,214,215,216,217,219,220,221,222,223,224,225,226,227,237,238,239,240,241,242,246,247,343,344,345,346,347,348])
# Translate the previous draft's paragraph slots to the current source's one-shorter body.
used={i if i <= 5 else i-1 for i in used}
used.update({18,27}) # Preserve the source ABSTRACT and TABLE OF CONTENTS headings.
# The existing design-flow prose is replaced with an editable architecture table below.
for idx in range(127,136):
 set_paragraph_text(P[idx],'')
for i,p in P.items():
 if i not in used and p.text.strip() and i not in range(0,16):
  set_paragraph_text(p,'')
# Turn only screenshot-only section breaks into continuous transitions. This keeps each page's original header/footer and page-number settings without forcing blank pages.
for idx in (53,81,242,347):
 p=P[idx]
 if p._p.pPr is not None and p._p.pPr.sectPr is not None:
  sec=p._p.pPr.sectPr
  typ=sec.find(qn('w:type'))
  if typ is None:
   typ=OxmlElement('w:type'); sec.insert(0,typ)
  typ.set(qn('w:val'),'continuous')
# Start requirements on a fresh chapter page after merging the two now-empty intro sections.
req_heading=P[84]
if req_heading._p.pPr is None:
 req_heading._p.insert(0,OxmlElement('w:pPr'))
if req_heading._p.pPr.find(qn('w:pageBreakBefore')) is None:
 req_heading._p.pPr.append(OxmlElement('w:pageBreakBefore'))
# Start the conclusion cleanly on a new page.
conclusion=P[342]
if conclusion._p.pPr is None:
 conclusion._p.insert(0,OxmlElement('w:pPr'))
if conclusion._p.pPr.find(qn('w:pageBreakBefore')) is None:
 conclusion._p.pPr.append(OxmlElement('w:pageBreakBefore'))
# Save text edits before adding native Word tables.
doc.save(path)
doc=Document(path)
# Convert the source's three raster table illustrations into editable Word tables.
# Find paragraph positions by image relationship in XML, before any insertions.
def image_target(paragraph):
 xml=paragraph._p.xml
 m=re.search(r'r:embed="([^"]+)"',xml)
 if not m:return None
 rel=paragraph.part.rels.get(m.group(1))
 return rel.target_ref if rel else None
specs={
 'image5.png':('Hardware Requirements',['No.','Component','Minimum','Recommended'],[
 ('1','Processor','64-bit dual-core CPU','Modern quad-core CPU'),('2','Memory','8 GB RAM','16 GB RAM'),('3','Storage','10 GB free for software and data','SSD with additional dataset capacity'),('4','Operating system','Windows 10 or later, 64-bit','Windows 11, 64-bit'),('5','Network','Internet for API retrieval','Stable broadband connection')]),
 'image6.png':('Software Requirements',['No.','Software','Role / requirement'],[
 ('1','Python 3.x','Runs ingestion, validation, analytics, and dashboard modules'),('2','MongoDB Community Server','Required local database service'),('3','PyMongo','Python driver for MongoDB'),('4','Pandas','Chunked CSV ingestion and tabular handling'),('5','Streamlit','Interactive web dashboard'),('6','Plotly','Interactive charts'),('7','Requests / python-dotenv','HTTP requests and environment configuration'),('8','Open-Meteo Archive API','Implemented historical weather source'),('9','MongoDB Compass','Optional GUI client for database inspection')]),
 'image7.png':('Default System Configuration',['Setting','Configured value'],[
 ('MongoDB URI','mongodb://127.0.0.1:27017/'),('Database','weather_analytics'),('Collections','weather_observations; ingestion_runs'),('Connection timeout','5000 ms default'),('Bulk batch size','1000 documents default')])
}
for p in list(doc.paragraphs):
 target=image_target(p)
 if target and target.split('/')[-1] in specs:
  label,headers,rows=specs[target.split('/')[-1]]
  # Remove image drawing but preserve paragraph location and section properties.
  for child in list(p._p):
   if child.tag==qn('w:r'):
    for el in list(child):
     if el.tag==qn('w:drawing'): child.remove(el)
    if not len(child): p._p.remove(child)
  caption=doc.add_paragraph(label)
  caption.style='Normal'
  caption.alignment=WD_ALIGN_PARAGRAPH.CENTER
  caption.paragraph_format.space_before=Pt(6)
  caption.paragraph_format.space_after=Pt(3)
  caption.paragraph_format.keep_with_next=True
  for r0 in caption.runs:
   r0.bold=True; r0.font.name='Times New Roman'; r0.font.size=Pt(10.5)
  p._p.addprevious(caption._p)
  table=doc.add_table(rows=1,cols=len(headers)); table.alignment=WD_TABLE_ALIGNMENT.CENTER; table.style='Table Grid'
  for cell,val in zip(table.rows[0].cells,headers): cell.text=val
  for vals in rows:
   cells=table.add_row().cells
   for c,val in zip(cells,vals): c.text=val
  for row_index,row in enumerate(table.rows):
   is_header=(row_index==0)
   for cell in row.cells:
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
    for par in cell.paragraphs:
     par.paragraph_format.space_after=Pt(0)
     for run in par.runs: run.font.size=Pt(9)
   row.height=None
  widths=({4:[0.45,1.25,2.35,2.35],3:[0.45,1.55,4.4],2:[2.25,4.15]}[len(headers)])
  table.autofit=False
  for row_index,row in enumerate(table.rows):
   is_header=(row_index==0)
   for col,cell in enumerate(row.cells):
    cell.width=Inches(widths[col])
    tcPr=cell._tc.get_or_add_tcPr()
    margins=OxmlElement('w:tcMar')
    for side,val in [('top','45'),('start','90'),('bottom','45'),('end','90')]:
     el=OxmlElement('w:'+side); el.set(qn('w:w'),val); el.set(qn('w:type'),'dxa'); margins.append(el)
    tcPr.append(margins)
    for par in cell.paragraphs:
     par.alignment=WD_ALIGN_PARAGRAPH.CENTER if col==0 or is_header else WD_ALIGN_PARAGRAPH.LEFT
     for run in par.runs:
      run.font.name='Times New Roman'; run.font.size=Pt(9); run.bold=is_header
    if is_header:
     shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),'E9DFD3'); cell._tc.get_or_add_tcPr().append(shd)
   if is_header:
    trPr=row._tr.get_or_add_trPr(); rep=OxmlElement('w:tblHeader'); rep.set(qn('w:val'),'true'); trPr.append(rep)

  p._p.addprevious(table._tbl)
# Add an editable, source-derived architecture diagram as a native Word table.
arch_anchor=next(p for p in doc.paragraphs if p.text.strip()=='The main components and data flow are:')
steps=[
 ('HISTORICAL WEATHER SOURCE','Open-Meteo Archive API or a compatible CSV file'),
 ('PYTHON INGESTION','weather_fetcher.py or import_data.py with Pandas'),
 ('VALIDATION AND NORMALIZATION','weather_utils.py parses timestamps and validates measurements'),
 ('BATCH PERSISTENCE','PyMongo submits unordered upserts in bounded batches'),
 ('LOCAL MONGODB COMMUNITY SERVER','weather_analytics stores observations and ingestion run records'),
 ('AGGREGATION AND ANALYTICS','MongoDB pipelines in analytics.py calculate filtered summaries'),
 ('INTERACTIVE DASHBOARD','Streamlit and Plotly present charts, filters, paginated records, and CSV export')]
arch=doc.add_table(rows=13,cols=1); arch.alignment=WD_TABLE_ALIGNMENT.CENTER; arch.autofit=False
arch.style='Table Grid'; arch.columns[0].width=Inches(6.25)
for i,(title,detail) in enumerate(steps):
 stage_row=2*i
 row=arch.rows[stage_row]; cell=row.cells[0]; cell.width=Inches(6.25); cell.text=''
 cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
 para=cell.paragraphs[0]; para.alignment=WD_ALIGN_PARAGRAPH.CENTER; para.paragraph_format.space_after=Pt(0); para.paragraph_format.space_before=Pt(0)
 r0=para.add_run(title); r0.bold=True; r0.font.name='Times New Roman'; r0.font.size=Pt(10)
 r1=para.add_run('\n'+detail); r1.font.name='Times New Roman'; r1.font.size=Pt(9)
 tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),'F5EFE8'); tcPr.append(shd)
 margins=OxmlElement('w:tcMar')
 for side,val in [('top','45'),('start','100'),('bottom','45'),('end','100')]:
  el=OxmlElement('w:'+side); el.set(qn('w:w'),val); el.set(qn('w:type'),'dxa'); margins.append(el)
 tcPr.append(margins)
 trPr=row._tr.get_or_add_trPr(); trPr.append(OxmlElement('w:cantSplit'))
 if i<len(steps)-1:
  ar=arch.rows[stage_row+1].cells[0]; ar.text='↓'; ar.width=Inches(6.25); ar.paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
  ar.paragraphs[0].paragraph_format.space_after=Pt(0); ar.paragraphs[0].paragraph_format.space_before=Pt(0)
  for rr in ar.paragraphs[0].runs: rr.font.name='Times New Roman'; rr.font.size=Pt(10); rr.font.color.rgb=__import__('docx').shared.RGBColor(128,77,43)
  tcPr=ar._tc.get_or_add_tcPr(); borders=OxmlElement('w:tcBorders')
  for edge in ('top','left','bottom','right','insideH','insideV'):
   el=OxmlElement('w:'+edge); el.set(qn('w:val'),'nil'); borders.append(el)
  tcPr.append(borders)
arch_anchor._p.addnext(arch._tbl)
figcap=doc.add_paragraph('Figure 3.1. Weather analytics data flow')
figcap.style='Normal'; figcap.alignment=WD_ALIGN_PARAGRAPH.CENTER
figcap.paragraph_format.space_before=Pt(3); figcap.paragraph_format.space_after=Pt(6)
for rr in figcap.runs: rr.italic=True; rr.font.name='Times New Roman'; rr.font.size=Pt(9)
arch._tbl.addnext(figcap._p)
# Put the evidence summary on the results continuation page in place of two short wrap-up paragraphs.
evidence_anchor=next(p for p in doc.paragraphs if p.text.strip().startswith('Table 5.1 summarizes the evidence'))
evidence_cap=doc.add_paragraph('Table 5.1. Project evidence and verification status')
evidence_cap.style='Normal'; evidence_cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
evidence_cap.paragraph_format.space_before=Pt(5); evidence_cap.paragraph_format.space_after=Pt(3); evidence_cap.paragraph_format.keep_with_next=True
for rr in evidence_cap.runs: rr.bold=True; rr.font.name='Times New Roman'; rr.font.size=Pt(10)
evidence=evidence_rows=[
 ('Evidence','Finding'),
 ('Sample CSV','Five Bengaluru hourly rows for 1 January 2023, 00:00–04:00; weather, humidity, precipitation, wind, pressure, cloud, and code fields.'),
 ('Automated tests','The project test run reported 19 passing tests; tests use mocked API responses and in-memory database fixtures.'),
 ('Live MongoDB','The local server was unreachable during this review, so live collection counts and aggregate measurements could not be checked.'),
 ('Reported dashboard values','The task brief reports 26,280 observations, 24.89 °C mean temperature, 3,704.1 mm rainfall, 2023 coverage, and Mumbai, Delhi, and Bengaluru; these were not independently verified.'),
 ('Implemented scope','The source registry contains ten cities and the dashboard code defines eight navigation areas; neither fact confirms records are loaded.')]
result_table=doc.add_table(rows=1,cols=2); result_table.alignment=WD_TABLE_ALIGNMENT.CENTER; result_table.style='Table Grid'; result_table.autofit=False
for cell,val in zip(result_table.rows[0].cells,evidence_rows[0]): cell.text=val
for vals in evidence_rows[1:]:
 cells=result_table.add_row().cells
 for c,val in zip(cells,vals): c.text=val
for ri,row in enumerate(result_table.rows):
 trPr=row._tr.get_or_add_trPr(); trPr.append(OxmlElement('w:cantSplit'))
 for ci,cell in enumerate(row.cells):
  cell.width=Inches((1.65,4.70)[ci]); cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
  tcPr=cell._tc.get_or_add_tcPr(); margins=OxmlElement('w:tcMar')
  for side,val in [('top','75'),('start','90'),('bottom','75'),('end','90')]:
   el=OxmlElement('w:'+side); el.set(qn('w:w'),val); el.set(qn('w:type'),'dxa'); margins.append(el)
  tcPr.append(margins)
  for para in cell.paragraphs:
   para.paragraph_format.space_after=Pt(1); para.alignment=WD_ALIGN_PARAGRAPH.LEFT
   for run in para.runs: run.font.name='Times New Roman'; run.font.size=Pt(8.5); run.bold=(ri==0 or ci==0)
  if ri==0:
   shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),'E9DFD3'); tcPr.append(shd)
evidence_anchor._p.addnext(evidence_cap._p); evidence_cap._p.addnext(result_table._tbl)
# Remove only obsolete screenshot drawings; keep the university logos and the replaced architecture image.
for p in doc.paragraphs:
 target=image_target(p)
 if target and any(x in target.lower() for x in ('image3.png','image4.png','image8.png','image9.png','image10.png','image11.png','image12.png','image13.png')):
  for el in list(p._p):
   if el.tag==qn('w:r'):
    for child in list(el):
     if child.tag==qn('w:drawing'): el.remove(child)
    if not len(el): p._p.remove(el)
# Remove obsolete body-floating diagrams and decorative marks whose screenshot anchors were deleted; recurring rules remain in the original header/footer parts.
for qi,p in enumerate(doc.paragraphs):
 if qi < 37: continue
 for drawing in list(p._p.xpath('.//w:drawing')):
  if not drawing.xpath('.//a:blip'):
   drawing.getparent().remove(drawing)
 for pict in list(p._p.xpath('.//w:pict')):
  pict.getparent().remove(pict)
# Remove empty screenshot spacer paragraphs after the front matter while preserving page/section breaks and remaining images.
for pi,p in enumerate(list(doc.paragraphs)):
 if p.text.strip(): continue
 if p._p.pPr is not None:
  if p._p.pPr.sectPr is not None or p._p.pPr.find(qn('w:pageBreakBefore')) is not None: continue
 if p._p.xpath('.//w:br[@w:type="page"]'): continue
 if '<w:drawing' in p._p.xml or '<w:pict' in p._p.xml: continue
 # Front matter spacing is part of the original cover/abstract/contents layout.
 if pi < 37: continue
 p._p.getparent().remove(p._p)
# Correct obsolete text in header/footer text boxes without reconstructing their drawing objects.
# The short running title fits the original header text box.
with zipfile.ZipFile(path,'r') as zin:
 package={n:zin.read(n) for n in zin.namelist()}
for name,blob in list(package.items()):
 if name.endswith('.xml'):
  package[name]=blob.replace(b'Virtual Machine Installation',b'Weather Data Analytics')
tmp=path.with_suffix('.pkg.docx')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as zout:
 for name,blob in package.items(): zout.writestr(name,blob)
tmp.replace(path)
# Correct old image content types / relationships that no longer have media targets.
rels=doc.part.rels
for rid,rel in list(rels.items()):
 if rel.reltype.endswith('/image') and not rel.is_external and not Path('word',rel.target_ref).exists():
  pass
# Add page-number update on open and retain dynamic fields if present.
settings=doc.settings.element
upd=settings.find(qn('w:updateFields'))
if upd is None:
 upd=OxmlElement('w:updateFields'); settings.append(upd)
upd.set(qn('w:val'),'true')
# The final document-level section used to start on a new page despite having no content.
doc.sections[-1].start_type=WD_SECTION.CONTINUOUS
# Keep the report body clear of the running header and its double rule on every body page.
for section in doc.sections[4:]:
 section.top_margin=Inches(0.92)
 section.bottom_margin=Inches(0.9)
 section.different_first_page_header_footer=False
 sectpr=section._sectPr
 old=sectpr.find(qn('w:pgBorders'))
 if old is not None: sectpr.remove(old)
 page_borders=OxmlElement('w:pgBorders')
 page_borders.set(qn('w:offsetFrom'),'text')
 page_borders.set(qn('w:display'),'allPages')
 for edge,space in [('bottom','0')]:
  border=OxmlElement('w:'+edge)
  border.set(qn('w:val'),'double'); border.set(qn('w:sz'),'6')
  border.set(qn('w:space'),space); border.set(qn('w:color'),'A35412')
  page_borders.append(border)
 page_margin=sectpr.find(qn('w:pgMar'))
 sectpr.insert(sectpr.index(page_margin)+1,page_borders) if page_margin is not None else sectpr.append(page_borders)
# Add the matching brown double rule below the running title, sized to the report text block.
header=doc.sections[4].header
header_rule=header.add_paragraph()
header_rule.paragraph_format.left_indent=Inches(0.45)
header_rule.paragraph_format.right_indent=Inches(0.23)
header_rule.paragraph_format.space_before=Pt(12)
header_rule.paragraph_format.space_after=Pt(0)
header_rule.paragraph_format.line_spacing=Pt(1)
header_rule.paragraph_format.widow_control=False
header_ppr=header_rule._p.get_or_add_pPr()
header_bdr=OxmlElement('w:pBdr')
header_bottom=OxmlElement('w:bottom')
for key,value in [('val','double'),('sz','6'),('space','2'),('color','A35412')]:
 header_bottom.set(qn('w:'+key),value)
header_bdr.append(header_bottom); header_ppr.append(header_bdr)
header_run=header_rule.add_run(' '); header_run.font.size=Pt(1)
# Avoid leaving a single opening line of the final introduction paragraph at the foot of its page.
for paragraph in doc.paragraphs:
 if paragraph.text.strip().startswith('The system is useful because it keeps data ingestion'):
  paragraph.paragraph_format.keep_together=True
 if paragraph.text.strip().startswith('By default, the application connects to mongodb://127.0.0.1:27017/'):
  paragraph.paragraph_format.space_before=Pt(14)
# Carry the running report title and department footer through the conclusion section.
doc.sections[-1].header.is_linked_to_previous=True
doc.sections[-1].footer.is_linked_to_previous=True
doc.save(path)
with zipfile.ZipFile(path,'r') as zin:
 package={n:zin.read(n) for n in zin.namelist()}
for name,blob in list(package.items()):
 if name.endswith('.xml'):
  package[name]=blob.replace(b'Virtual Machine Installation',b'Weather Data Analytics')
# Move the department and page-number footer boxes slightly below the footer rule.
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}
for name,blob in list(package.items()):
 if not (name.startswith('word/footer') and name.endswith('.xml') and not name.endswith('.rels')):
  continue
 root=etree.fromstring(blob)
 text=''.join(root.xpath('.//w:t/text()',namespaces=ns))
 if 'DEPARTMENT OF CSE (AI)' not in text:
  continue
 for anchor in root.xpath('.//wp:anchor[wp:docPr[@name="Textbox 13" or @name="Textbox 14"]]',namespaces=ns):
  position=anchor.find('wp:positionV',ns)
  offset=position.find('wp:posOffset',ns) if position is not None else None
  if offset is not None:
   offset.text=str(int(offset.text)+8*12700)
 package[name]=etree.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
tmp=path.with_suffix('.final.docx')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as zout:
 for name,blob in package.items(): zout.writestr(name,blob)
tmp.replace(path)
print('saved',path)






