#!/bin/bash
# remove compact version of first page of a pdf file, which likely contains the paper title

PDF_NAME="$1"

# extract first page to text, remove blanks, and convert into lowercase
pdftotext -f 1 -l 1 -eol unix -raw $PDF_NAME - |
    tr -d '[:space:]' |
    tr '[:upper:]' '[:lower:]'
