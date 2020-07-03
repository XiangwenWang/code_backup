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
from bs4 import BeautifulSoup

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
    driver.get("https://csgofast.com/#game/x50")
    time.sleep(4)

    try:
        driver.find_element_by_css_selector('button.btn-yellow.yes')
    except NoSuchElementException:
        driver.save_screenshot('csgofast_x50.png')
    time.sleep(2)
    return driver


def find_profit(eletag):
    if len(eletag.find_all('span', {"class": "x50-bets-stats__item-bet win"})) > 0:
        return 1
    else:
        return 0


def get_id_bet_dict(color_bets):
    id_bet_dict = {}
    for userblock in color_bets.findAll('li', {'class': 'x50-bets-stats__item'}):
        userid = userblock.find('div', {'class': 'x50-bets-stats__item-content'}
                                )['data-userid']
        userbet = int(userblock.find(
            'span', {'class': 'coins-new__value'}).text)
        if userid in id_bet_dict:
            print('error: player already placed a bet')
        id_bet_dict[userid] = userbet
    return id_bet_dict


def get_bets(content, logs, cur, conn, timestamp):

    if len(re.findall('x50-bets-stats__item-bet win', content)) == 0:
        return None

    round_index = re.findall('<span class="x50-room__hash-value" data-bind="text:md5">([0-9a-z]{56})</span>',
                             content)[0]

    round_index = round_index[20:-20]
    if round_index in logs:
        return None
    logs.add(round_index)

    soup = BeautifulSoup(content, "lxml")

    return_ratio = {'blue': 2, 'red': 3, 'green': 5, 'gold': 50}
    win_color, raw_bets, profits = None, {}, {}

    for color in return_ratio:
        c_bets = soup.find('div', {"class": "x50-bets-stats__column_type_%s" % color,
                                   "data-bind": "attr:{class: columnStyle}"})
        c_profit = find_profit(c_bets)
        if c_profit > 0:
            win_color = color
        raw_bets[color] = c_bets
        profits[color] = c_profit

    exec_str = """
               INSERT INTO x50_test
               (gametime, userid, roundid, color, betvalue, roundcolor, win, profit)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
               """
    for color in return_ratio:
        outcome_ratio, win = (return_ratio[color] - 1, 1) if color == win_color else (-1, 0)
        color_bets = get_id_bet_dict(raw_bets[color])
        for uid in color_bets:
            userID = hashlib.md5(uid.encode('utf-8')).hexdigest()[8:-8]
            betValue = color_bets[uid]
            netincome = betValue * outcome_ratio
            curr_values = (timestamp, userID, round_index, color, betValue,
                           win_color, win, netincome)
            # print(curr_values)
            cur.execute(exec_str, curr_values)

    conn.commit()
    return 1


def main():

    conn = psycopg2.connect(database="gamble", user="test",
                            password="test", host="127.0.0.1", port="5432")
    cur = conn.cursor()

    try:
        logs = joblib.load('analyzed_x50.pkl')
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
                joblib.dump(logs, 'analyzed_x50.pkl')
            driver.save_screenshot('csgofast_x50.png')

        time.sleep(2)

    joblib.dump(logs, 'analyzed_x50.pkl')
    conn.close()


if __name__ == '__main__':
    main()
