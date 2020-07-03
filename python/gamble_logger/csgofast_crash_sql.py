#!/usr/bin/python
# -*- coding: utf-8 -*-

from selenium import webdriver
import time
import socket
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from datetime import datetime
import re
import psycopg2
import hashlib
import joblib
import pytz
import sys

if sys.version_info[0] < 3:
    from urllib2 import URLError
    from httplib import BadStatusLine
else:
    from urllib.error import URLError
    from http.client import BadStatusLine


def refresh_driver():

    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(firefox_options=options)
    driver.get("https://csgofast.com/#game/crash")
    time.sleep(5)

    try:
        driver.find_element_by_css_selector('button.btn-yellow.yes')
    except NoSuchElementException:
        driver.save_screenshot('csgofast_crash.png')
    time.sleep(3)
    return driver


def get_bets(content, logs, cur, conn, timestamp):

    content = content.split(
        '<div class="crashed" style="display: block;">Crash:</div>', 1)
    if len(content) < 2:
        return None
    content = content[1]

    crashed_value = re.findall(
        r'<span class="value">([0-9\.]*)x</span>', content)
    if not crashed_value:
        return None

    round_index = int(re.findall(u'<span class="game-num">№<span class="value">([0-9]+)</span></span>',
                                 content)[0])
    if round_index in logs:
        return None
    logs.add(round_index)

    crashed_value = int(float(crashed_value[0]) * 100)

    regex_bet = re.compile(r'<li class="player-bet (win|lose)".+?' +
                           r'data-userid="([0-9]*)".+?<div class="bet-value">' +
                           r'([0-9\.]*)</div>.+?<div class="bet-coef">([0-9\.]*)x</div>.+?' +
                           r'<div class="bet-profit">([0-9\.]*)</div>.+?</li>', re.DOTALL)
    bet_log = re.findall(regex_bet, content)

    winlose_dict = {'win': 1, 'lose': 0}
    exec_str = """
               INSERT INTO crash_test
               (gametime, userid, roundid, risk, betvalue, roundcoef, win, profit)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
               """

    for b in bet_log:
        win = winlose_dict[b[0]]
        userID = hashlib.md5(b[1].encode('utf-8')).hexdigest()[8:-8]
        betValue = int(b[2])
        risk = int(float(b[3]) * 100)
        netincome = int(b[4]) if win else -betValue
        curr_values = (timestamp, userID, round_index, risk, betValue,
                       crashed_value, win, netincome)
        cur.execute(exec_str, curr_values)

    conn.commit()
    return 1


def main():

    conn = psycopg2.connect(database="gamble", user="test",
                            password="test", host="127.0.0.1", port="5432")
    cur = conn.cursor()

    try:
        logs = joblib.load('analyzed_crash.pkl')
    except (IOError, OSError, EOFError):
        logs = set()

    driver = refresh_driver()
    last_dt = None

    while True:

        try:
            content = driver.page_source
        except URLError:
            try:
                driver.close()
            except (WebDriverException, URLError, BadStatusLine, socket.error):
                pass
            driver = refresh_driver()
            print('Refreshed page at %s' % time.strftime(
                "%Y-%m-%d %H:%M:%S", time.gmtime()))

        dt = int((datetime.utcnow().replace(tzinfo=pytz.UTC) -
                  datetime(1970, 1, 1, tzinfo=pytz.UTC)).total_seconds())

        res = get_bets(content, logs, cur, conn, dt)
        if res:
            if not last_dt:
                last_dt = dt
            elif dt - last_dt >= (3600 * 12):
                last_dt = dt
                driver = refresh_driver()
                print('Refreshed page at %s' % time.strftime(
                      "%Y-%m-%d %H:%M:%S", time.gmtime()))
                joblib.dump(logs, 'analyzed_crash.pkl')
            driver.save_screenshot('csgofast_crash.png')

        time.sleep(2)

    joblib.dump(logs, 'analyzed_crash.pkl')
    conn.close()


if __name__ == '__main__':
    main()
