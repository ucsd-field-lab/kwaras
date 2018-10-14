# -*- coding: utf-8 -*-
"""Unicode csv stream

based on code from python csv module documentation
"""

import cStringIO
import codecs
import csv

# these are the defaults for *writing* csv files only
csv.excel.lineterminator = '\n'
csv.excel.delimiter = ','

csv.excel_tab.quoting = csv.QUOTE_ALL


class CsvRow(list):
    """
    A named list, indexed by both position and by dict-type string keys,
    like named tuples, but overloading row[key] rather than using row.key notation
    """

    def __init__(self, elems, fieldnames):
        self.fieldnames = fieldnames
        self._dict = dict(zip(self.fieldnames, elems) + zip(range(len(elems)), elems))
        list.__init__(self, elems)

    def __getitem__(self, key):
        return self._dict[key]

    def items(self):
        return [(k, self._dict[k]) for k in self.fieldnames]

    def get(self, key, d=None):
        return self._dict.get(key, d)


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """

    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

    def readlines(self, size):
        return [line.encode("utf-8") for line in self.reader.readlines(size)]

    def seek(self, pos):
        self.reader.seek(pos)


class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file @f,
    which is either a filename or an open filestream encoded in the given encoding.

    If @dialect or @fieldnames is not provided, we will try to guess them.
    Setting @fieldnames=True skips the guessing and reads the first line as fieldnames.
    Setting @fieldnames=False skips the guessing and uses "V1", "V2", etc.
    """

    def __init__(self, f, dialect=None, fieldnames=None, encoding="utf-8", **kwds):

        if isinstance(f, (str, unicode)):
            fstream = open(f, "rb")
        else:
            fstream = f

        r = UTF8Recoder(fstream, encoding)
        sniffdata = '\n'.join(r.readlines(500))
        r.seek(0)

        if dialect is None:
            try:
                dialect = csv.Sniffer().sniff(sniffdata, ",\t")
            except csv.Error:
                dialect = csv.excel
        if not fieldnames and fieldnames is not False:
            try:
                fieldnames = csv.Sniffer().has_header(sniffdata)
            except csv.Error:
                fieldnames = True

        self.reader = csv.reader(r, dialect=dialect, **kwds)

        if fieldnames is True:
            header = self.reader.next()
            print header
            fieldnames = [unicode(s, "utf-8") for s in header]
        elif not fieldnames:
            cols = len(sniffdata.split('\n')[0].split(dialect.delimiter))
            fieldnames = [u"V" + str(i) for i in range(cols)]
        self.fieldnames = tuple([unicode(n) for n in fieldnames])

    def next(self):
        row = [unicode(s, "utf-8") for s in self.reader.next()]
        return CsvRow(row, self.fieldnames)

    def __iter__(self):
        return self


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file @f,
    which is either a filename or an open filestream encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", mode="wb", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        if isinstance(f, (str, unicode)):
            self.stream = open(f, mode)  # if passed a string, assume it's a filename
            # self.filename = f
        else:
            self.stream = f  # otherwise assume it is file-like stream
            # self.filename = f.name
        self.encoder = codecs.getincrementalencoder(encoding)()

    def write(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.write(row)

    def close(self):
        self.stream.close()


if __name__ == '__main__':

    import unittest
    import tempfile
    import random


    class TestUtfCsv(unittest.TestCase):

        def setUp(self):

            self.file = tempfile.TemporaryFile()
            self._testdat = u"áçcèñt"

        def test_quoted_csv(self):
            uw = UnicodeWriter(self.file, dialect=csv.excel_tab)
            header = [random.choice(self._testdat) + str(i)
                      for i in range(10)]
            uw.write(header)
            for row in range(10):
                uw.write([str(i) + random.choice(""" '"`:-/\t""")
                          for i in range(10)])
            self.file.seek(0)

            print
            print "A utf-8 file with special characters"
            ur = UnicodeReader(self.file)
            print ' | '.join(ur.fieldnames)
            print ur.next()
            print '\t'.join(ur.next())

        def test_headed_csv(self):

            uw = UnicodeWriter(self.file)
            header = [random.choice(self._testdat) + str(i)
                      for i in range(10)]
            uw.write(header)
            for row in range(10):
                uw.write([str(i)
                          # random.choice(self._testdat)
                          for i in range(10)])
            self.file.seek(0)

            print
            print "A utf-8 file with headers"
            ur = UnicodeReader(self.file)
            print ' | '.join(header)
            print ' | '.join(ur.fieldnames)
            print ur.next()

            self.assertTrue(ur.fieldnames == tuple(header))

        def test_vaguely_headed_csv(self):

            uw = UnicodeWriter(self.file)
            header = [random.choice(self._testdat) + str(i)
                      for i in range(10)]
            uw.write(header)
            for row in range(10):
                uw.write([str(i) + random.choice(self._testdat)
                          for i in range(10)])

            self.file.seek(0)
            print
            print "A utf-8 file with unclear headers"
            ur = UnicodeReader(self.file)
            print ' | '.join(header)
            print ' | '.join(ur.fieldnames)
            print ur.next()

            self.assertFalse(ur.fieldnames == tuple(header))

            self.file.seek(0)
            print
            print "Believe that the top line is headers"
            ur = UnicodeReader(self.file, fieldnames=True)
            print ' | '.join(header)
            print ' | '.join(ur.fieldnames)
            print ur.next()

            self.assertTrue(ur.fieldnames == tuple(header))


    try:
        unittest.main()
    except SystemExit:
        pass
