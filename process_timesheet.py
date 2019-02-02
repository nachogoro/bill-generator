#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import calendar
import os
import subprocess
from datetime import datetime, timedelta

MAX_HOURS_PER_WEEK = 35
MEAN_HOURS_PER_DAY = MAX_HOURS_PER_WEEK / 5

def get_worked_hours_per_day(csv_path, target_month):
    """
    Returns a dictionary of date-worked_hours.
    The keys range from the beginning of the week of the first of the month
    until the last day of the month
    """
    # Parse the CSV
    with open(csv_path, 'r') as src:
        content = [l.strip() for l in src.readlines()]

    # Find first line of dates
    for i, line in enumerate(content):
        if line.split(',')[-1] == 'TOTAL':
            break

    content = content[i:]

    hours_per_day = dict()

    first_of_month = datetime.strptime(
        '01/%02d/%04d' % (target_month.month, target_month.year), '%d/%m/%Y')

    dow, last_day = calendar.monthrange(target_month.year, target_month.month)

    range_start = first_of_month - timedelta(days=dow)
    range_end = datetime.strptime(
        '%02d/%02d/%04d' % (last_day, target_month.month, target_month.year),
        '%d/%m/%Y')

    for cindex in range(0, int(len(content)/2)):
        # Pair date with worked hours, and ommit the last column (TOTAL)
        dates = [d for d in content[2*cindex].split(',') if d][:-1]
        hours = [h for h in content[2*cindex+1].split(',') if h][:-1]

        for dindex, date_str in enumerate(dates):
            date = datetime.strptime(date_str, '%d/%m/%Y')

            if not (range_start <= date <= range_end):
                continue

            if date in hours_per_day:
                raise Exception('Duplicate information for ' + date)

            # If there is no data for this date, assume zero hours
            if dindex < len(hours):
                hours_in_day = float(hours[dindex])
            else:
                hours_in_day = 0

            hours_per_day[date] = hours_in_day

    return hours_per_day


def get_billable_days(target_month):
    """
    Returns the list of days that are billable (i.e. a weekday) for a given
    month in a year
    """
    _, last_day = calendar.monthrange(target_month.year, target_month.month)
    result = []
    for day in range(1, last_day + 1):
        date = datetime.strptime(
            '%02d/%02d/%04d' % (day, target_month.month, target_month.year),
            '%d/%m/%Y')

        if 0 <= date.weekday() <= 4:
            result.append(date)

    return result


def generate_useful_information(output_file, hours_per_day, target_month):
    billable_days = get_billable_days(target_month)
    billed_days = [d for d,h in hours_per_day.items()
                   if h > 0 and d.month == target_month.month]

    # Billed days that are actually unbillable (working on weekends)
    billed_unbillable = sorted(list(set(billed_days).difference(billable_days)))

    # Billable days that have not been billed (maybe holidays, off-sick)
    unbilled_billable = sorted(list(set(billable_days).difference(billed_days)))

    end_of_month = sorted(hours_per_day.keys())[-1]
    beginning_of_week = sorted(hours_per_day.keys())[0]
    end_of_week = beginning_of_week + timedelta(days=6)

    underworked_weeks = []
    overworked_weeks = []

    # Only analyse weeks which start and end before the end of the month
    while end_of_week <= end_of_month:
        billed_hours = sum([h for d,h in hours_per_day.items()
                            if beginning_of_week <= d <= end_of_week])

        number_of_absent_days = sum([1 for d,h in hours_per_day.items()
                                     if (beginning_of_week <= d <= end_of_week
                                         and h == 0)])
        min_workable_hours = (MAX_HOURS_PER_WEEK
                              - number_of_absent_days*MEAN_HOURS_PER_DAY)

        if billed_hours < min_workable_hours:
            underworked_weeks.append((beginning_of_week,
                                      min_workable_hours - billed_hours))
        elif billed_hours > MAX_HOURS_PER_WEEK:
            overworked_weeks.append((beginning_of_week,
                                     billed_hours - MAX_HOURS_PER_WEEK))

        beginning_of_week += timedelta(days=7)
        end_of_week = beginning_of_week + timedelta(days=6)

    # Write the report
    with open(output_file, 'w', encoding='utf-8') as dst:
        if len(billed_unbillable) == 0:
            print('✔ No unbillable days have been billed', file=dst)
        else:
            print(
                '⚠️ WARNING: The following days were weekends but have been billed:',
                file=dst)
            for unbillable in billed_unbillable:
                print('\t%s' % unbillable.strftime('%d/%m/%Y'), file=dst)
        print(file=dst)

        if len(unbilled_billable) == 0:
            print('✔ No billable days have been left unbilled', file=dst)
        else:
            print(
                '⚠️ WARNING: The following days were week days but have not been billed:',
                file=dst)
            for unbilled in unbilled_billable:
                print('\t%s' % unbilled.strftime('%d/%m/%Y'), file=dst)
        print(file=dst)

        if len(underworked_weeks) == 0:
            print('✔ No weeks have been underworked', file=dst)
        else:
            print('⚠️ WARNING: The following weeks have been underworked:',
                  file=dst)
            for week in underworked_weeks:
                print('\t%s (%.2f hours)'
                      % (week[0].strftime('%d/%m/%Y'), week[1]),
                      file=dst)
        print(file=dst)

        if len(overworked_weeks) == 0:
            print('✔ No weeks have been overworked', file=dst)
        else:
            print('⚠️ WARNING: The following weeks have been over-worked: ',
                  file=dst)
            for week in overworked_weeks:
                print('\t%s (%.2f hours)'
                      % (week[0].strftime('%d/%m/%Y'), week[1]),
                      file=dst)
        print(file=dst)


def generate_pdf(
    latex_template, target_month, worked_hours, hourly_rate, output_dir):

    tex_name = os.path.join(
        output_dir,
        '%s - Invoice.tex' % target_month.strftime('%y.%m'))

    _, last_day_of_the_month = calendar.monthrange(target_month.year,
                                                   target_month.month)

    # Read the template
    with open(latex_template, 'r') as src:
        filedata = src.read()

    # List of keywords to be replaced in the LaTeX template
    replacement_dict = {
        'CURRENTDATE': '%02d/%s' % (last_day_of_the_month, target_month.strftime('%m/%Y')),
        'CURRENTINVOICENUMBER': '%02d/%04d' % (target_month.month, target_month.year),
        'CURRENTMONTH': target_month.strftime('%B'),
        'CURRENTYEAR': target_month.strftime('%Y'),
        'WORKEDHOURS': '%.2f' % float(worked_hours),
        'HOURLYRATE': str(hourly_rate),
        'TOTALAMOUNT': '%.2f' % float(worked_hours*hourly_rate)
    }

    # Replace the placeholder strings
    for to_replace, replacement in replacement_dict.items():
        filedata = filedata.replace(to_replace, replacement)

    # Write the file out again
    with open(tex_name, 'w') as dst:
        dst.write(filedata)

    # Generate the pdf
    subprocess.call(
        ['pdflatex', '-output-directory', output_dir,
         '-interaction=nonstopmode', tex_name],
        stdout=subprocess.PIPE)

    # Remove every file related to the bill except the .pdf
    tex_name_no_ext,_ = os.path.splitext(os.path.basename(tex_name))
    for file_in_dir in [os.path.join(output_dir, f) for f in os.listdir(output_dir)]:
        file_name_no_ext, file_ext = os.path.splitext(os.path.basename(file_in_dir))
        if file_name_no_ext == tex_name_no_ext and file_ext != '.pdf':
            os.remove(file_in_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv_path',
                        help='Path to the CSV with the hour log',
                        type=str,
                        default='Time sheet.csv',
                        action='store')
    parser.add_argument('--month', help='Month to bill (mm/yyyy)',
                        type=str,
                        default=datetime.today().strftime('%m/%Y'),
                        action='store')
    parser.add_argument('--rate', help='Hourly rate in pounds',
                        type=int,
                        action='store')
    parser.add_argument('--stats', help='Output file with stats',
                        type=str,
                        default='stats-%s.txt' % datetime.today().strftime('%m%Y'),
                        action='store')
    parser.add_argument('--latex_template',
                        help='LaTeX file with the bill template',
                        type=str,
                        default='billing_template.tex',
                        action='store')
    parser.add_argument('--output_directory',
                        help='Directory to place the output files',
                        type=str,
                        default='.',
                        action='store')
    args = parser.parse_args()

    target_month = datetime.strptime(args.month, '%m/%Y')

    hours_per_day = get_worked_hours_per_day(args.csv_path, target_month)

    total_of_hours_in_month = sum(
        [h for d,h in hours_per_day.items() if d.month == target_month.month])

    generate_useful_information(
        os.path.join(args.output_directory, args.stats),
        hours_per_day,
        target_month)

    generate_pdf(
        args.latex_template, target_month, total_of_hours_in_month, args.rate,
        args.output_directory)


if __name__ == '__main__':
    main()
