import os
import re
# import sys
import bibtexparser
import glob
import PyPDF2
from pathvalidate import sanitize_filename
# from pprint import pprint
# import subprocess

################################ CONFIGURATION #################################

def make_filename(bibentry):
    clean_title = bibentry['title'].strip()
    clean_title = sanitize_filename(clean_title, "")
    return "{} {}.pdf".format(bibentry['year'], clean_title)

##################################### CODE #####################################

KNOWN_FILES = set()
UNKNOWN_FILES = []

def compact_string(src):
    # https://stackoverflow.com/questions/8270092/remove-all-whitespace-in-a-string-in-python
    return re.sub(r"\s+", "", src).lower()

def collect_bib_entries():
    bibdb = []

    # https://stackoverflow.com/questions/3964681/find-all-files-in-a-directory-with-extension-txt-in-python/14001395
    for bib in glob.glob("*.bib"):
        print("Collecting BibTeX entries from '{}'".format(bib))
        with open(bib) as bibtex_file:
            bibdb += bibtexparser.load(bibtex_file).entries

    unmatched = []

    # remove dobule braces
    for entry in bibdb:
        title = entry['title']
        # https://stackoverflow.com/questions/19954593/python-checking-a-strings-first-and-last-character
        if title.startswith('{') and title.endswith('}'):
            # https://stackoverflow.com/questions/3085382/python-how-can-i-strip-first-and-last-double-quotes
            entry['title'] = title[1:-1]
        filename = make_filename(entry)
        if os.path.exists(filename):
            # entry already has matched pdf file
            KNOWN_FILES.add(filename)
        else:
            unmatched.append(entry)

    return unmatched

# https://medium.com/@rqaiserr/how-to-convert-pdfs-into-searchable-key-words-with-python-85aab86c544f
def read_pdf_first_page_compact(pdfname):
    # pypdf can't read some pdf and will produce random characters. however pdftotext works fine.
    # return subprocess.check_output(["bash", "firstpage.sh", pdfname]).decode(sys.stdout.encoding)

    pdfFileObj = open(pdfname, 'rb')
    # The pdfReader variable is a readable object that will be parsed
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    # https://github.com/mstamy2/PyPDF2/issues/51
    if pdfReader.isEncrypted:
        pdfReader.decrypt('')
    ret = compact_string(pdfReader.getPage(0).extractText())
    pdfFileObj.close()
    return ret

# find bibtex entry in the given bibtex database for a given pdf
def find_bib_entry(bibdb, pdfname):
    compactfirstpage = read_pdf_first_page_compact(pdfname)

    longestmatch = None

    for entry in bibdb:
        compacttitle = compact_string(entry['title'])

        if compacttitle in compactfirstpage:
            # print('Found BibTeX entry "{}" for "{}"'.format(entry['title'], pdfname))
            if longestmatch == None or len(longestmatch['title']) < len(entry['title']):
                if longestmatch:
                    print("Warning: {} has multiple title matches.".format(pdfname))
                longestmatch = entry

    return longestmatch

def update_pdf(bibdb, pdfname):
    entry = find_bib_entry(bibdb, pdfname)
    if entry:
        newname = make_filename(entry)
        print('"{}" -> "{}"'.format(pdfname, newname))
        os.rename(pdfname, newname)
    else:
        UNKNOWN_FILES.append(pdfname)

def update_all_pdfs(folder):
    print("Updating pdf filenames in {}".format(folder))
    os.chdir(folder)
    bibdb = collect_bib_entries()
    print("{} BibTeX entries not matched with any pdf files:".format(len(bibdb)))
    for entry in bibdb:
        print("    '{}'".format(entry['title']))
    print("Ignoring {} known pdf files".format(len(KNOWN_FILES)))

    # pprint(bibdb)
    for pdf in glob.glob("*.pdf"):
        filename = os.path.basename(pdf)
        if not filename in KNOWN_FILES:
            # print('Updating name for {}'.format(pdf))
            try:
                update_pdf(bibdb, pdf)
            except Exception as e:
                print(e)

    if UNKNOWN_FILES:
        print("No BibTex entry found for the following pdf files:")
        for unknown in UNKNOWN_FILES:
            print("    '{}'".format(unknown))

def download_all_pdfs(folder):
    pass

update_all_pdfs(".")
