#!/bin/bash

function is_last_weekday_of_month {
	today=$(date +'%d')
	month=$(date +'%m')
	year=$(date +'%Y')
	read -r dow day < <(date -d "$year/$month/1 +1 month -1 day" "+%u %d")
	last_weekday=$(( day - ( (dow>5)?(dow-5):0 ) ))
	if [[ "${today}" == "${last_weekday}" ]]; then
		return 0
	else
		return 1
	fi
}

# Download the time sheet
wget -O "Time sheet.xlsx" DOWNLOAD-LINK

# Convert it to CSV
libreoffice --headless --convert-to csv --outdir . "./Time sheet.xlsx"

# Generate the .pdf and the stats
python3 process_timesheet.py --csv_path Time\ sheet.csv \
	--month $(date +"%m/%Y") \
	--rate HOURLY-RATE \
	--latex_template billing_template.tex

# If it is the last working day of the month, e-mail the results
is_last_weekday_of_month
if [ "$?" -eq 0 ]; then
	invoice="$(date +"%y.%m") - Invoice.pdf"
	stats="stats-$(date +"%m%Y").txt"
	echo "Sending ${invoice} with stats: ${stats}"

	python3 ./email-pdf.py --fromaddr your-from-addr@gmail.com \
		--toaddr your-receiver-addr@gmail.com \
		--attachment "$(date +"%y.%m") - Invoice.pdf" \
		stats-$(date +"%m%Y").txt
else
	echo "Not sending e-mail (today is $(date +"%d/%m/%Y"))"
fi

# Delete the generated files
rm *Invoice.pdf stats-*.txt
