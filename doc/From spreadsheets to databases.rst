********************************
From spreadsheets to databases
********************************

.. index::
   single: sps2db.py
   pair: spreadsheet; csv
   pair: spreadsheet; ods
   pair: spreadsheet; xls
   pair: spreadsheet; xlsx
   pair: spreadsheet; csvz
   pair: spreadsheet; tsv
   pair: spreadsheet; tsvz
   pair: spreadsheet; xlrd
   pair: spreadsheet; xlwt
   single: pyexcel
   single: --override
   single: --append


This section describes the details of :program:`sps2db.py`. For a quick example of its usage, the reader is referred to Section [[Populating databases]].

:program:`sps2db.py` is used to populate a sqlite3 database with data extracted from a spreadsheet. The following formats are recognized: :const:`csv`, :const:`csvz`, :const:`tsv`, :const:`tsvz`, :const:`xls`, :const:`xlrd`, :const:`xlwt`, :const:`xlsx` and :const:`ods`. The following table shows the commands that should be used to install the required extensions to :mod:`pyexcel`

   +---------------------------------+------------------------+
   +          **Command**            |       **Formats**      |
   +---------------------------------+------------------------+
   | ``$ pip install pyexcel-io``    |   csv, csvz, tsv, tsvz |
   |                                 |                        |
   | ``$ pip install pyexcel-xls``   |   xls, xlrd, xlwt      |
   |                                 |                        |
   | ``$ pip install pyexcel-xlsx``  |   xlsx                 |
   |                                 |                        |
   | ``$ pip install pyexcel-ods3``  |   ods                  |
   |                                 |                        |
   | ``$ pip install pyexcel-ods``   |   ods                  |
   +---------------------------------+------------------------+

To extract data from a spreadsheet in a systematic way into a sqlite3 database two parameters are mandatory:

* A configuration file describing what data is extracted from the spreadsheet and how it is inserted into the database. Other information, such as the spreadsheet to read and the specific sheetname to process should be given also in case they are not explicitly indicated in the configuration file. However, to ease reuse of configuration files it is possible to explicitly override the specifcations of the configuration file with the flag ``--override``. 

* The name of the sqlite3 database to create. In case a file with the same name exists, execution immediately halts. Moreover, if a database table already exists when processing the configuration file, an error is also raised. However, this might be inconvenient as the same configuration file might be inserting data from different parts of the same spreadsheet into the same table. To allow this sort of operations, the flag ``--append`` can be used.


===================
Configuration files
===================

Configuration files consist of a sequence of database tables each described in a single block between ccurly brackets and preceded by its name:


.. code:: text

  region {
   ... 
  }

  demography {
   ...
  }

Each block describes the different columns of the database table in different lines all ended with a semicolon. The minimum information required to process data from the spreadsheet is:

1. First, the range to process which could be either a cell, ``$A3`` or an interval of cells such as ``$B17:$B25``.
