
# Set variables used for normalizing tier structure

TEMPLATE = "new/tx1.eaf"

# Set variables used for exporting EAF to CSV
FILE_DIR = "/Users/lucien/Data/Mixtec/"        # working directory
OLD_EAFS = 'Transcriptions/test/'  # apply a filter within working directory
NEW_EAFS = "new/"                      # subdirectory as destination
CSV = "Transcriptions/min-new.csv"                    # destination exported CSV file

EXPORT_FIELDS = ["Broad", "Ortho", "NewOrtho", "Phonetic",    # List of fields to include
                 "UttWGloss", "UttMGloss",
                 "Spanish", "English", "Note"]

# Set variables for exporting to HTML
META = FILE_DIR + 'MixtecoMetadata.csv'  # From Google doc
WAV = FILE_DIR + 'WAV' # WAV input
WWW = 'F://ELAN Corpus/www'  # www data output
CLIPS = '/Users/lucien/Data/Kwaras/Mixtec/new/clips'  # wav clip output
PG_TITLE = "Raramuri Corpus"
NAV_BAR = """<div align="right">
    <a href="index.html">Corpus</a> - <a href="dict.xhtml">Dictionary</a>
    </div>"""



FILE_DIR = "/Users/lucien/Data/Mixtec/"
CSV = FILE_DIR + 'Transcriptions/min-new.csv'  # ELAN export file
META = FILE_DIR + 'MixtecoMetadata.csv'  # From Google doc
eaf_dir = FILE_DIR + 'Transcriptions/test/'  # EAF input
wav_dir = FILE_DIR + 'WAV'  # WAV input
clip_dir = '/Users/lucien/Data/Kwaras/Mixtec/new/clips'  # wav clip output
meta_dir = '/Users/lucien/Data/Kwaras/Mixtec/new'  # csv data output
page_title = "Nieves Mixtec / Tu'un Nda'vi Corpus"
NAV_BAR = """<div align="right">
<a href="corpus.html">Corpus</a> - <a href="dict.html">Diccionario</a> -
<a href="cuentos/index.html">Cuentos</a> - <a href="rel.html">Enlaces</a>
</div>"""
# limit and give order for exported fields
_EXPORT_FIELDS = []