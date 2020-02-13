# Introduction #

``spsbot`` is a Python package that automates the population of a
spreadsheet/sqlite database from data extracted from a sqlite
database/spreadsheet. To this end, it comes with two Python scripts `sps2db.py`
and `db2sps.py`.

Both programs are driven by a configuration file which specifies what data
should be extracted and how to store it in the designated target.

While this software acknowledges a wide variety of spreadsheet formats
(including `csv`, `ods`, `xls`, `xlsx`, etc.), only sqlite3 databases can be
used.


# Installation #

Download the software cloning the git repository with the following command:

    $ git clone https://github.com/clinaresl/spsbot.git

a directory called `spsbot` will be automatically created. Go to that directory
and execute the script `setup.py` as indicated below:

    $ cd spsbot
    $ sudo python3 ./setup.py install

In case this software is being reinstalled, make sure to add `--force`
to overwrite the previous package.


# License #

spsbot is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

spsbot is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License
along with spsbot.  If not, see <http://www.gnu.org/licenses/>.


# Author #

Carlos Linares Lopez <carlos.linares@uc3m.es>
