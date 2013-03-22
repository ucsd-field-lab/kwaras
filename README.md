kwaras -- tools for ELAN corpus management
======


Tools
-------------------------
* process/web.py -- converts ELAN data (exported into tab-delimited text format) into an html table with jQuery interface, linked to sound clips
* process/timealign.py -- finds sound clips within larger sound files, creating CSV annotation files (to be imported into ELAN)
* formats/eaf.py, lang/* -- functions for making bulk edits in a corpus of ELAN files

Dependencies
-------------------------
The web process depends on jQuery DataTables, including the plugins TableTools and ColVis. The tested versions of these modules are included in the web/ directory.

