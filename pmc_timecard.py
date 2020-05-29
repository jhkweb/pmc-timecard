import pandas
import openpyxl
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.styles.protection import Protection
import os
import csv
from datetime import datetime, timedelta
import holidays
import dropbox
from shutil import copyfile
import ad_query


dbx = dropbox.Dropbox(os.environ['DBACCESSTOKEN'])
dbx.files_download_to_file('Activity.csv', '/JHK/Activity/Daily/Activity.csv')

start_date = datetime.today() - timedelta(days=1)

# copy activity report so we have a history as it gets overwritten everyday
copyfile('Activity.csv', r'Activity Backups\Activity{}.csv'.format(start_date.strftime("%m-%d-%Y")))

data = pandas.read_csv('Activity.csv')


def get_holiday_dates():
    us_holidays = holidays.US(years=datetime.now().year)
    double_time_holidays = ["New Year's Day", "Memorial Day", "Independence Day (Observed)", "Labor Day", "Veterans Day", "Thanksgiving", "Christmas Day"]
    holiday_datetime = []

    for holiday in us_holidays.items():
        if holiday[1] in double_time_holidays:
            if holiday[1] == "Thanksgiving":
                holiday_datetime.append(holiday[0])
                holiday_datetime.append(holiday[0] + timedelta(days=1))
            else:
                holiday_datetime.append(holiday[0])
    return holiday_datetime


def new_timecard(filename):
    # check AD for user title, fall back to csv if not found
    role = "UNKNOWN"
    title = ad_query.get_user_title(filename)
    if title:
        title = title.replace(' Service Technician', '').strip()
        role = title
    else:
        tech_roles = csv.reader(open('techroles.csv'), delimiter=',')
        for r in tech_roles:
            if r[0] == filename:
                role = r[1]
    # need to implement DropBox api to upload files vs. saving them into local DropBox mapped folder
    # save_dir = r'C:/Users/cspaulding/Dropbox (JH Kelly)/Personal/Timecards/{}/{}'.format(role, start_date.strftime("%m-%d-%Y"))
    save_dir = r'C:/Temp/Timecards/{}/{}'.format(role, start_date.strftime("%m-%d-%Y"))
    if not os.path.exists(save_dir):
        print('Creating Sub Dir: {}'.format(save_dir))
        os.makedirs(save_dir)
    return "{}/{}.xlsx".format(save_dir, filename)


dt_holidays = get_holiday_dates()

data['Status Date'] = pandas.to_datetime(data['Status Date'])

data = data.sort_values(['Tech', 'Status Date'], ascending=(True, True))
df = pandas.DataFrame(columns=['Status', 'Date Created', 'Customer ID', 'Work Order #', 'Job Description', 'Status Date', 'Status Changes', 'Location', 'Tech'])

# export sorted df debugging
data.to_csv('Results.csv')

template_path = 'Template.xlsx'
template = openpyxl.load_workbook(template_path, read_only=False)

input_row_index = 3
driving = False
daily_hours = 0
temp_task_date = start_date
previous_row_emp = ''

for index, row in data.iterrows():
    # future, need to implement a fix for DST
    current_row_date = row['Status Date'].to_pydatetime() - timedelta(hours=7)

    # only handle entries from the current day
    if current_row_date.day != start_date.day or current_row_date.month != start_date.month \
            or current_row_date.year != start_date.year:
        continue

    current_row_emp = row['Tech'].replace('  ', ' ')
    current_row_event = row['Status Changes']
    current_row_wo = row['Work Order #']
    current_row_task = row['Location']
    current_row_taskname = row['Location']
    task_date = current_row_date.strftime('%b-%d')
    task_time = current_row_date.strftime('%H:%M:%S')
    task_datetime = current_row_date

    if current_row_emp != previous_row_emp:
        grand_total_hours = 0
        try:
            time_ws['G{}'.format(input_row_index + 1)] = '= SUM(G3:G{})'.format(input_row_index)
            time_ws['F{}'.format(input_row_index + 1)].value = 'Total Hours'
            time_ws.protection.sheet = True
            columns = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
            for col in columns:
                if col == 'K' or col == 'L':
                    for i in range(3, input_row_index + 32):
                        time_ws['{}{}'.format(col, i)].protection = Protection(locked=False)
                else:
                    for i in range(input_row_index + 2, input_row_index + 32):
                        time_ws['{}{}'.format(col, i)].protection = Protection(locked=False)
            timecard.save(filename)
        except NameError as e:
            print(e)
        driving = False
        daily_hours = 0
        filename = new_timecard(current_row_emp)
        template = openpyxl.load_workbook(template_path, read_only=False)
        template.save(filename=new_timecard(current_row_emp))
        timecard = openpyxl.load_workbook(filename, read_only=False)
        time_ws = timecard['Timecard']
        input_row_index = 3
        previous_row_emp = current_row_emp

    time_ws['A1'].value = current_row_emp

    time_ws['A{}'.format(input_row_index)].value = task_date
    time_ws['B{}'.format(input_row_index)].value = current_row_taskname
    time_ws['C{}'.format(input_row_index)].value = current_row_wo

    time_ws['K{}'.format(input_row_index)].value = "No"
    dv = DataValidation(type="list", formula1='"No,Yes"', allow_blank=False)
    time_ws.add_data_validation(dv)
    dv.add(time_ws['K{}'.format(input_row_index)])

    if current_row_event == 'Driving':
        if not driving:
            time_ws['D{}'.format(input_row_index)].value = task_datetime
            driving = True
    elif current_row_event == 'On Site':
        time_ws['E{}'.format(input_row_index)].value = task_datetime
    elif current_row_event == 'Job Complete' or current_row_event.startswith('Susp.'):
        time_ws['F{}'.format(input_row_index)].value = task_datetime
        try:
            drive_start = time_ws['D{}'.format(input_row_index)].value
        except TypeError as e:
            print(e)
        try:
            on_site_start = time_ws['E{}'.format(input_row_index)].value
        except TypeError as e:
            print(e)
        job_complete = time_ws['F{}'.format(input_row_index)].value
        if drive_start:
            on_site_start = drive_start
        try:
            total_hours = job_complete - on_site_start
            total_hours = round(total_hours.total_seconds() / 60 / 60, 2)
            time_ws['G{}'.format(input_row_index)] = '= SUM(H{}:J{})'.format(input_row_index, input_row_index)
            if temp_task_date.day == current_row_date.day:
                daily_hours += total_hours
            else:
                daily_hours = 0
            # double time on holidays
            if current_row_date.date() in dt_holidays:
                time_ws['J{}'.format(input_row_index)].value = daily_hours
            elif daily_hours <= 8:
                # overtime if weekend, Saturday and Sunday
                if current_row_date.weekday() == 5 or current_row_date.weekday() == 6:
                    time_ws['I{}'.format(input_row_index)].value = total_hours
                    # print(index, daily_hours, total_hours)
                else:
                    # standard time before 8 hours
                    time_ws['H{}'.format(input_row_index)].value = total_hours
            elif daily_hours > 8:
                if current_row_date.weekday() == 5 or current_row_date.weekday() == 6:
                    time_ws['I{}'.format(input_row_index)].value = daily_hours
                else:
                    time_ws['I{}'.format(input_row_index)].value = daily_hours - 8
                    if total_hours - (daily_hours - 8) <= 0:
                        time_ws['H{}'.format(input_row_index)].value = 0
                    else:
                        time_ws['H{}'.format(input_row_index)].value = total_hours - (daily_hours - 8)
        except TypeError:
            time_ws['G{}'.format(input_row_index)].value = 'ERROR'
        driving = False
        input_row_index += 1
        temp_task_date = current_row_date
        # print(index, temp_task_date, current_row_date)
    try:
        timecard.save(filename)
    except OSError as e:
        print(e)
