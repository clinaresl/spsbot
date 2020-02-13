****************
Intro
****************

.. index::
   single: sps2db.py
   single: db2sps.py
   pair: spreadsheet; csv
   pair: spreadsheet; ods
   pair: spreadsheet; xls
   pair: spreadsheet; xlsx

*spsbot* is a Python package that automates the population of a spreadsheet/sqlite database from data extracted from a sqlite database/spreadsheet. To this end, it comes with two Python scripts :program:`sps2db.py` and :program:`db2sps.py`.

Both programs are driven by a configuration file which specifies what data should be extracted and how to store it in the designated target.

While this software acknowledges a wide variety of spreadsheet formats (including :const:`csv`, :const:`ods`, :const:`xls`, :const:`xlsx`, etc.), only sqlite3 databases can be used.

The following sections provide full information about the functionalities provided by both programs. Nevertheless, a quick tour is included also for the impatient reader.
