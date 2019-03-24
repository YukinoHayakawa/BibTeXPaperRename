import os
import re
import bibtexparser
import glob
from pathvalidate import sanitize_filename
import fitz
import urllib
import pathlib

################################ CONFIGURATION #################################

OPEN_RENAMED = True

def make_filename(bibentry):
    clean_title = bibentry['title'].strip()
    clean_title = sanitize_filename(clean_title, "")
    return "{} {}.pdf".format(bibentry['year'], clean_title)

##################################### CODE #####################################

KNOWN_FILES = set()
UNKNOWN_FILES = []
BASE_PATH = ""
RENAMED = set()

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

    # remove double braces
    for entry in bibdb:
        title = entry['title']
        # https://stackoverflow.com/questions/19954593/python-checking-a-strings-first-and-last-character
        if title.startswith('{') and title.endswith('}'):
            # https://stackoverflow.com/questions/3085382/python-how-can-i-strip-first-and-last-double-quotes
            entry['title'] = title[1:-1]

    return bibdb

def collect_bib_entries_unmatched():
    bibdb = collect_bib_entries()
    unmatched = []

    for entry in bibdb:
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

    # pdfFileObj = open(pdfname, 'rb')
    # # The pdfReader variable is a readable object that will be parsed
    # pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    # # https://github.com/mstamy2/PyPDF2/issues/51
    # if pdfReader.isEncrypted:
    #     pdfReader.decrypt('')
    # ret = compact_string(pdfReader.getPage(0).extractText())
    # pdfFileObj.close()
    # return ret

    doc = fitz.open(pdfname)
    page = doc.loadPage(0)
    text = page.getText("text")
    doc.close()
    return compact_string(text)


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
                    # print("Warning: {} has multiple title matches.".format(pdfname))
                    pass
                longestmatch = entry

    return longestmatch

def update_pdf(bibdb, pdfname):
    entry = find_bib_entry(bibdb, pdfname)
    if entry:
        if len(entry['title'].split()) < 3:
            print("Warning: '{}' matched with a short title '{}' which may be a common phrase.".format(pdfname, entry['title']))
        newname = make_filename(entry)
        print("    '{1}' <- '{0}'".format(pdfname, newname))
        print("        Open: {}".format(pathlib.Path(os.path.join(BASE_PATH, newname)).as_uri()))
        os.rename(pdfname, newname)
        if OPEN_RENAMED:
            os.startfile(newname)
        RENAMED.add(newname)
    else:
        UNKNOWN_FILES.append(pdfname)

def update_all_pdfs(folder):
    global BASE_PATH
    BASE_PATH = os.path.abspath(folder)
    print("Updating pdf filenames in {}".format(folder))
    os.chdir(folder)
    bibdb = collect_bib_entries_unmatched()
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

    # collect unmatched bibtex entries after renaming
    bibdb = collect_bib_entries_unmatched()
    if bibdb:
        print("{} BibTeX entries not matched with any pdf files:".format(len(bibdb)))
        for entry in bibdb:
            print("    '{}'".format(entry['title']))
            print("        Google Scholar: https://scholar.google.com/scholar?q={}".format(urllib.parse.quote_plus(entry['title'])))
            # print("        Sci-Hub: https://scholar.google.com/scholar?q={}".format(urllib.parse.quote_plus(entry['title'])))

    if UNKNOWN_FILES:
        print("{} pdf files not matched with any BibTex entries:".format(len(UNKNOWN_FILES)))
        for unknown in UNKNOWN_FILES:
            print("    '{}' ({})".format(unknown, pathlib.Path(os.path.join(BASE_PATH, unknown)).as_uri()))

def download_all_pdfs(folder):
    pass

def rename_single_pdf(pdfpath):
    fullpath = os.path.abspath(pdfpath)
    global BASE_PATH
    BASE_PATH = os.path.dirname(fullpath)
    os.chdir(BASE_PATH)
    bibdb = collect_bib_entries()
    update_pdf(bibdb, os.path.basename(fullpath))
