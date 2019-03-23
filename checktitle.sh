#!/bin/bash
# checks if a given pdf contains the given title in the first page

PDF_NAME="$1"
# removes blanks from title and convert to lower case for easier matching
COMPACT_TITLE=$(echo $2 | tr -d '[:blank:]' | tr '[:upper:]' '[:lower:]')

# extract first page to text, remove blanks, and convert into lowercase
pdftotext -f 1 -l 1 -eol unix -raw $PDF_NAME - |
    tr -d '[:blank:]' |
    tr '[:upper:]' '[:lower:]' |
    grep -q $COMPACT_TITLE

exit_status=$?
if [ $exit_status -eq 1 ]; then
    # echo "not found"
    : # nop
else
    echo "Matched title \"$2\" in \"$PDF_NAME\""
fi

exit $exit_status
