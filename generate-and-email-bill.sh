#!/bin/bash

WORKING_DIR="MY-WORKING-DIRECTORY"
DOM=$(date +'%d')
MONTH=$(date +'%m')
YEAR=$(date +'%Y')
YEAR_TWO_DIGITS=$(date +'%y')
TODAY=$(date +"%d/%m/%Y")
STATS_FILE="${WORKING_DIR}/stats-${MONTH}${YEAR}.txt"

MONTHS_WORD=(dummy January February March April May June July August September \
    October November December)

function is_last_weekday_of_month {
    read -r dow day < <(date -d "${YEAR}/${MONTH}/1 +1 month -1 day" "+%u %d")
    last_weekday=$(( day - ( (dow>5)?(dow-5):0 ) ))
    echo "Last weekday of ${MONTH}/${YEAR} is ${day}/${MONTH}/${YEAR}"
    if [[ "${DOM}" == "${last_weekday}" ]]; then
        return 0
    else
        return 1
    fi
}

# Download the time sheet
wget -O "${WORKING_DIR}/Time sheet.xlsx" \
    DOWNLOAD-LINK

# Convert it to CSV
libreoffice --headless \
    --convert-to csv \
    --outdir "${WORKING_DIR}" \
    "${WORKING_DIR}/Time sheet.xlsx"

# Generate the .pdf and the stats
python3 "${WORKING_DIR}/process_timesheet.py" \
    --csv_path "${WORKING_DIR}/Time sheet.csv" \
    --month "${MONTH}/${YEAR}" \
    --rate HOURLY-RATE \
    --stats "${STATS_FILE}" \
    --output_directory "${WORKING_DIR}" \
    --latex_template "${WORKING_DIR}/billing_template.tex"

# If it is the last working day of the month, e-mail the results
is_last_weekday_of_month
if [ "$?" -eq 0 ]; then
    INVOICE="${WORKING_DIR}/${YEAR_TWO_DIGITS}.${MONTH} - Invoice.pdf"
    echo "Sending ${INVOICE} with stats: ${STATS_FILE}"

    python3 "${WORKING_DIR}/email-pdf.py" \
        --fromaddr your-from-addr@gmail.com \
        --toaddr your-receiver-addr@gmail.com \
        --attachment "${INVOICE}" \
        --subject "Invoice for ${MONTHS_WORD[${MONTH}]}, ${YEAR}" \
        "${STATS_FILE}"
else
    echo "Not sending e-mail (today is ${TODAY})"
fi

# Delete the generated files
rm "${WORKING_DIR}"/*Invoice.pdf "${WORKING_DIR}"/stats-*.txt
