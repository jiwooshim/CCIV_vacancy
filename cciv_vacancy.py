import sys
import time
import requests
import getpass
import os
import pandas as pd
from os.path import exists, join
from webbot import Browser
from datetime import datetime
from tabulate import tabulate

current_dir = os.getcwd()
csv_dir = join(current_dir, "csv_data")

def decalre_web():
    global web
    web = Browser(showWindow=False)
    web.go_to('https://banweb.cityu.edu.hk/pls/PROD/twgkpswd_cityu.P_WWWLogin')


def get_user_detail():
    usrid = input("..Input user ID: ")
    pw = getpass.getpass(prompt='..Input password: ')
    return usrid, pw


def get_html_user_iden():
    html_source = web.get_page_source()
    html_source = html_source.split("\n")
    for line in html_source:
        if '<td class="dedefault">' in line:
            if 'name' in line:
                useriden = line[47:].split('"')[0]
                if useriden.startswith("User"):
                    return useriden


def log_in(id, pw):
    web.type(id)
    web.type(pw, into='Password', id='passwordFieldId')
    web.click(' Login ')


def browse_to_dest():
    course_id = "1501"
    lp_break = True
    break_idx = 0

    while lp_break:
        while "mainmnu" in web.get_current_url().lower():
            web.type('master', id='keyword_in_id')
            web.click('Go')
            web.click('Master Class Schedule')
            print("..Opening master class schedule")
            break_idx += 1
            if break_idx > 29:
                lp_break = False
                break

        web.switch_to_tab(2)
        while "selterm" in web.get_current_url().lower():
            web.click("Submit Term")
            break_idx += 1
            if break_idx > 29:
                lp_break = False
                break

        web.switch_to_tab(2)
        while "crsesearch" in web.get_current_url().lower():
            web.click('Search Class')
            print("..Searching class")
            break_idx += 1
            if break_idx > 29:
                lp_break = False
                break

        time.sleep(3)
        web.switch_to_tab(2)
        while "getcrse" in web.get_current_url().lower():
            web.switch_to_tab(2)
            web.click(course_id)
            print("..Enquire for {}".format(course_id))
            break_idx += 1
            if break_idx > 29:
                lp_break = False
                break

        web.switch_to_tab(1)
        web.close_current_tab()
        web.switch_to_tab(1)
        break


def get_source():
    html_source = web.get_page_source()
    return html_source


def html_to_csv(html_source):
    df_list = pd.read_html(html_source)
    df = df_list[-3]
    print("..Extraction complete, result shown below\n{\n %s\n}" % df)
    if not exists(csv_dir):
        os.makedirs(csv_dir)

    csv_name = "{}.csv".format(datetime.now().strftime("%Y.%m.%d_%H:%M:%S"))
    print("..Exported to %s" % csv_name)
    df.to_csv(join(csv_dir, csv_name))


def csv_latest():
    csv_list = os.listdir(csv_dir)
    os.chdir(csv_dir)
    csv_list.sort(key=os.path.getmtime)
    latest = csv_list[-1]
    os.chdir(current_dir)

    return latest


def csv_extract(csv_fname):
    os.chdir(csv_dir)
    with open(csv_fname) as csv_file:
        df = pd.read_csv(csv_file)

    tb1 = df.loc[df['Section'] == 'TB1']
    tb2 = df.loc[df['Section'] == 'TB2']
    tb3 = df.loc[df['Section'] == 'TB3']
    tb4 = df.loc[df['Section'] == 'TB4']

    global tb1_row, tb2_row, tb3_row, tb4_row

    tb1_row = tb1
    tb2_row = tb2
    tb3_row = tb3
    tb4_row = tb4

    class_full = ['Full', 'FULL', 'Ful', 'full', 'ful', 'FUL']

    if tb1.at[57, 'Avail'] not in class_full:
        ifttt("tb1")

    if tb2.at[58, 'Avail'] not in class_full:
        ifttt("tb2")

    if tb3.at[59, 'Avail'] not in class_full:
        ifttt("tb3")

    if tb4.at[60, 'Avail'] not in class_full:
        ifttt("tb4")


def ifttt(section):
    print("\n..Vacancy Found. Start IFTTT")
    try:
        current_row = section + "_row"
        print("Current table: {}\n{}".format(section, eval(current_row)))
    except:
        pass

    def email_alert(first, second, third):
        report = {"value1": first, "value2": second, "value3": third}
        requests.post("https://maker.ifttt.com/trigger/ilovecake/with/key/hG1wtP7p2xyFzls05J9y06xUE3nIvNpgY50KHCZ9vcT",
                      data=report)
        print("..Request sent to IFTTT. Please check associated email")

    if section == "tb1":
        pretty_tb1 = tabulate(tb1_row, headers='keys', tablefmt='simple')
        email_alert("TB1", "10871", pretty_tb1)
    if section == "tb2":
        pretty_tb2 = tabulate(tb2_row, headers='keys', tablefmt='simple')
        email_alert("TB2", "10872", pretty_tb2)
    if section == "tb3":
        pretty_tb3 = tabulate(tb3_row, headers='keys', tablefmt='simple')
        email_alert("TB3", "12283", pretty_tb3)
    if section == "tb4":
        pretty_tb4 = tabulate(tb4_row, headers='keys', tablefmt='simple')
        email_alert("TB4", "12733", pretty_tb4)


def main(usrid, pw):
    decalre_web()
    print("..Attempting login")
    log_in(usrid, pw)
    print("..Login success")
    browse_to_dest()
    print("..Browse to the destination success")
    source = get_source()
    html_to_csv(source)
    latest = csv_latest()
    csv_extract(latest)


if __name__ == "__main__":
    start_time = time.time()
    elapsed_time = start_time - start_time
    seconds = 30 * 60
    init = 1
    print("Accessing AIMS.. Current time: ", datetime.now().strftime("%H:%M:%S"))
    usrid, pw = get_user_detail()

    while True:
        if init == 1:
            main(usrid, pw)
            init = 0

        elif elapsed_time < seconds:
            current_time = time.time()
            elapsed_time = current_time - start_time

            sys.stdout.write("\r")
            sys.stdout.write(
                "..Next check will be in {:.0f} minutes. Elapsed time: {:.0f}min / {:.0f}min | Current time: {}".format(
                    seconds / 60, elapsed_time / 60, seconds / 60, datetime.now().strftime("%H:%M:%S")))
            sys.stdout.flush()
            time.sleep(1)
            continue

        else:
            print("\n\nChecking vacancies.. Current time: ", datetime.now().strftime("%H:%M:%S"))
            try:
                main(usrid, pw)
            except Exception as e:
                print(e)
                decalre_web()
                continue
