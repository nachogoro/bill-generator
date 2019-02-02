# Bill generator
## What's this project about
This project automatically generates bills in .pdf from information on the
hours worked in an Excel file, and e-mails them to an specified address.

## Motivation
I need to generate monthly bills for my contract. Normally, this would require
logging into the hour-tracking system the last working day of the month and
checking my logged hours. I would then manually update my Word template with
the current month, the worked hours and the total amount owed. **This takes
about 3 minutes.**

Of course, spending 3 minutes once a month is unacceptable, so I decided to
automate the whole thing. This project downloads an Excel file from a given
URL, converts it to .csv and parses it. It then analyses the data and generates
some stats, mostly to ensure that nothing was improperly logged into the
system. With that data, it updates a LaTeX template and compiles it to .pdf.
Finally, if it is the last working day of the month, it e-mails the resulting
.pdf along with the generated stats to my e-mail, where I can verify that
everything is correct and forward it to whom it may concern.

I do not expect this to be useful as it is to anyone but myself.

## Using the tool
Before using the tool, modify the following strings in the corresponding files:
* `your-from-addr@gmail.com` in `email-pdf.py` and `generate-and-email-bill.sh`
  to the default sender e-mail address.
* `your-receiver-addr@gmail.com` in `email-pdf.py` and
  `generate-and-email-bill.sh` to the address where e-mails must be sent.
* `INSERT-PASSWORD-HERE` in `email-pdf.py` to the password of the default
  sender address.
* `MY-WORKING-DIRECTORY` in `generate-and-email-bill.sh` to the directory
  containing the scripts.
* `DOWNLOAD-LINK` in `generate-and-email-bill.sh` to the URL containing the
  .xlsx file with the logged hours.
* `HOURLY-RATE` in `generate-and-email-bill.sh` to the hourly rate for your
  services.
* `billing_template.tex` in `generate-and-email-bill.sh` to the path of the
  LaTeX billing template.

Once that is done, simply run:
`./generate-and-email-bill.sh`

This works best as a daily crontab entry.

## Dependencies
This project requires libreoffice with a European date locale for appropriate conversion from .xlsx to .csv.
It also requires python3.
