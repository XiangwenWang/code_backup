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
    driver.get("https://csgofast.com/#game/double")
    time.sleep(5)

    try:
        driver.find_element_by_css_selector('button.btn-yellow.yes')
    except NoSuchElementException:
        driver.save_screenshot('csgofast_double.png')
    time.sleep(3)
    return driver


def find_profit(eletag):
    if len(eletag.find_all('span', {"class": "coins-component game-bets-value loss"})) > 0:
        return 0
    elif len(eletag.find_all('span', {"class": "coins-component game-bets-value win"})) > 0:
        return 1
    else:
        print('error: Neither a win nor a loss')
        return -1


def get_id_bet_dict(color_bets):
    id_bet_dict = {}
    for userblock in color_bets.findAll('li', {'class': 'bonus-game-bet showed'}):
        userid = userblock.find('div', {'class': 'bet-user-info middle-block'}
                                )['data-userid']
        userbet = int(userblock.find('div', {'class': 'coins-component bet-value'}
                                     ).text)
        if userid in id_bet_dict:
            print('error: player already placed a bet')
        id_bet_dict[userid] = userbet
    return id_bet_dict


def get_bets(content, logs, cur, conn, timestamp):

    if len(re.findall('"coins-component game-bets-value win"', content)) == 0:
        return None

    round_index = int(re.findall(u'<span class="game-num">№<span class="value">([0-9]+)</span></span>',
                                 content)[0])
    if round_index in logs:
        return None
    logs.add(round_index)

    soup = BeautifulSoup(content, "lxml")

    black_bets = soup.find('li', {"class": "column black"})
    black_profit = find_profit(black_bets)

    red_bets = soup.find('li', {"class": "column red"})
    red_profit = find_profit(red_bets)

    green_bets = soup.find('li', {"class": "column green"})
    green_profit = find_profit(green_bets)

    return_ratio = {'green': 14 * green_profit,
                    'red': 2 * red_profit,
                    'black': 2 * black_profit}
    for c in return_ratio:
        if return_ratio[c] > 0:
            win_color = c

    exec_str = """
               INSERT INTO double_test
               (gametime, userid, roundid, color, betvalue, roundcolor, win, profit)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
               """

    id_bet_json = {}
    id_bet_json['red'] = get_id_bet_dict(red_bets)
    id_bet_json['green'] = get_id_bet_dict(green_bets)
    id_bet_json['black'] = get_id_bet_dict(black_bets)

    for color in id_bet_json:
        win = 1 if win_color == color else 0
        for uid in id_bet_json[color]:
            userID = hashlib.md5(uid.encode('utf-8')).hexdigest()[8:-8]
            betValue = id_bet_json[color][uid]
            netincome = betValue * (return_ratio[color] - 1)
            curr_values = (timestamp, userID, round_index, color[0], betValue,
                           win_color[0], win, netincome)
            cur.execute(exec_str, curr_values)

    conn.commit()
    return 1


def main():

    conn = psycopg2.connect(database="gamble", user="test",
                            password="test", host="127.0.0.1", port="5432")
    cur = conn.cursor()

    try:
        logs = joblib.load('analyzed_double.pkl')
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
                joblib.dump(logs, 'analyzed_double.pkl')
            driver.save_screenshot('csgofast_double.png')

        time.sleep(2)

    joblib.dump(logs, 'analyzed_double.pkl')
    conn.close()


if __name__ == '__main__':
    main()
