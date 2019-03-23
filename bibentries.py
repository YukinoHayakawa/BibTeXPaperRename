import os
import subprocess
import re
import sys
import bibtexparser
import glob

def collect_bib_entries(folder):
    bib_database = []

    # https://stackoverflow.com/questions/3964681/find-all-files-in-a-directory-with-extension-txt-in-python/14001395
    for bib in glob.glob(folder + "/*.bib"):
        with open(bib) as bibtex_file:
            bib_database += bibtexparser.load(bibtex_file).entries

    return bib_database

# find bibtex entry in the given bibtex database for a given pdf
# pdf should be in wsl path
def find_bib_entry(bibdb, pdf):
    # https://stackoverflow.com/questions/5902485/can-i-have-subprocess-call-write-the-output-of-the-call-to-a-string/5902720
    firstpage = subprocess.check_output(["bash", "firstpage.sh", pdf]).decode(sys.stdout.encoding)
    # print(firstpage)

    for entry in bibdb:
        title = entry['title']
        # https://stackoverflow.com/questions/19954593/python-checking-a-strings-first-and-last-character
        if title.startswith('{') and title.endswith('}'):
            # https://stackoverflow.com/questions/3085382/python-how-can-i-strip-first-and-last-double-quotes
            title = title[1:-1]

        # https://stackoverflow.com/questions/8270092/remove-all-whitespace-in-a-string-in-python
        compacttitle = re.sub(r"\s+", "", title).lower()

        filename = entry['year'] + ' ' + title
        print(filename)

        # result = subprocess.run(["bash", "checktitle.sh", pdf, title])
        # print(compacttitle)
        if compacttitle in firstpage:
            print('Found bibtex entry "{}" for "{}"'.format(title, pdf))
            return entry

    return None
