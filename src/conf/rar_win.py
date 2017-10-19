# Set variables used for normalizing tier structure

TEMPLATE = "new/tx1.eaf"

# Set variables used for exporting EAF to CSV
FILE_DIR = "F://ELAN corpus/"  # working directory
OLD_EAFS = ("", "in", "co", "el", "tx")[0]  # apply a filter within working directory
NEW_EAFS = "new/"  # subdirectory as destination
CSV = "rar-new.csv"  # destination exported CSV file

EXPORT_FIELDS = ["Broad", "Ortho", "NewOrtho", "Phonetic",  # List of fields to include
                 "UttWGloss", "UttMGloss",
                 "Spanish", "English", "Note"]

# Set variables for exporting to HTML
META = 'F://ELAN Corpus/metadata_raramuri_2011.txt'  # From Google doc
WAV = 'F://ELAN Corpus/WAV'  # WAV input
WWW = 'F://ELAN Corpus/www'  # www data output
CLIPS = 'F://ELAN Corpus/www/clips'  # wav clip output
PG_TITLE = "Raramuri Corpus"
NAV_BAR = """<div align="right">
    <a href="index.html">Corpus</a> - <a href="dict.xhtml">Dictionary</a>
    </div>"""
