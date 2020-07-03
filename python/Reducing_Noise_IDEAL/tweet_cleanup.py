#!/usr/bin/env python
# coding: utf-8
import sys
import re
import avro
import avro.schema
from avro.datafile import DataFileReader, DataFileWriter
from avro.io import DatumReader, DatumWriter
import json
from nltk.stem.lancaster import LancasterStemmer
import time
import uuid

'''
Codes for cleaning up tweets locally
Author: X.W, P.C
'''

st = LancasterStemmer()
__doc_id__ = 'charlie_hebdo_S'
__stop_word__ = [u'i', u'me', u'my', u'myself', u'we', u'our', u'ours',
                 u'ourselves', u'you', u'your', u'yours', u'yourself', u'yourselves', u'he',
                 u'him', u'his', u'himself', u'she', u'her', u'hers', u'herself', u'it', u'its',
                 u'itself', u'they', u'them', u'their', u'theirs', u'themselves', u'what', u'which',
                 u'who', u'whom', u'this', u'that', u'these', u'those', u'am', u'is', u'are', u'was',
                 u'were', u'be', u'been', u'being', u'have', u'has', u'had', u'having', u'do', u'does',
                 u'did', u'doing', u'a', u'an', u'the', u'and', u'but', u'if', u'or', u'because', u'as',
                 u'until', u'while', u'of', u'at', u'by', u'for', u'with', u'about', u'against', u'between',
                 u'into', u'through', u'during', u'before', u'after', u'above', u'below', u'to', u'from',
                 u'up', u'down', u'in', u'out', u'on', u'off', u'over', u'under', u'again', u'further',
                 u'then', u'once', u'here', u'there', u'when', u'where', u'why', u'how', u'all', u'any',
                 u'both', u'each', u'few', u'more', u'most', u'other', u'some', u'such', u'no', u'nor',
                 u'not', u'only', u'own', u'same', u'so', u'than', u'too', u'very', u's', u't', u'can',
                 u'will', u'just', u'don', u'should', u'now']

with open('profanity_en.txt') as f:
    __profanity_words__ = f.read()[:-1].split('\n')
f.close()


def validate(url):  # task 4
    return 1


def cleanup(tweet):
    # task 1
    # remove emoticon
    try:  # Wide UCS-4
        EmoRegexp = re.compile(u'['
                               u'\U0001F300-\U0001F64F'
                               u'\U0001F680-\U0001F6FF'
                               u'\u2600-\u26FF\u2700-\u27BF]+',
                               re.UNICODE)
    except re.error:  # Narrow UCS-2
        EmoRegexp = re.compile(u'('
                               u'\ud83c[\udf00-\udfff]|'
                               u'\ud83d[\udc00-\ude4f\ude80-\udeff]|'
                               u'[\u2600-\u26FF\u2700-\u27BF])+',
                               re.UNICODE)
    tweet = EmoRegexp.sub(' ', tweet)
    tweet = re.sub(r' \'s', ' s', tweet)
    tweet = re.sub(r'\'s', '', tweet)
    # task 2
    # Remove non-alphanumeric characters
    HashtagRegexp = r'(?<=^|(?<=[^a-zA-Z0-9-\.]))#([A-Za-z_]+[A-Za-z0-9_]+)'
    UserhandleRegexp = r'(?<=^|(?<=[^a-zA-Z0-9-\.]))@([A-Za-z_]+[A-Za-z0-9_]+)'
    UrlRegexp = r'(?P<url>https?://[a-zA-Z0-9\./-]+)'
    Hashtaglist = re.findall(HashtagRegexp, tweet)
    for hashtag in Hashtaglist:
        tweet = tweet.replace('#' + hashtag, '')
    Userhandlelist = re.findall(UserhandleRegexp, tweet)
    for userhandle in Userhandlelist:
        tweet = tweet.replace('@' + userhandle, '')
    url_list = re.findall(UrlRegexp, tweet)
    for url in url_list:
        tweet = tweet.replace(url, '')
    tweet = re.sub(r'([^\s\w]|_)+', '', tweet)  # task 5 included
    clean_tweet_only = tweet
    for hashtag in Hashtaglist:
        tweet = tweet + ' #' + hashtag
    for userhandle in Userhandlelist:
        tweet = tweet + ' @' + userhandle
    # task 3
    # validating url
    ValidUrlRegexp = re.compile(r'^(?:http|ftp)s?://'  # http:// or https://
                                # domain...
                                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
                                r'localhost|'  # localhost...
                                # ...or ip
                                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                                r'(?::\d+)?'  # optional port
                                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    for url in url_list:
        if ValidUrlRegexp.match(url) and validate(url):
            tweet = tweet + ' ' + url
    tweet = re.sub(' +', ' ', tweet)
    clean_tweet_only = ''.join(
        [w if len(w) > 0 else '' for w in clean_tweet_only])
    if len(clean_tweet_only) == 0:
        return (None, None, None, None, None, None)
    clean_tweet_only = ''.join(
        [w if ord(w) < 128 else ' ' for w in clean_tweet_only])
    clean_tweet_only = ' '.join(
        [word for word in clean_tweet_only.split(' ') if word.lower() not in __stop_word__])
    ProfanityRegexp = re.compile(
        r'(?<=^|(?<=[^a-zA-Z0-9-\.]))(' + '|'.join(__profanity_words__) + r')(?=$|\W)', re.IGNORECASE)
    clean_tweet_only = re.sub(' +', ' ', clean_tweet_only)
    clean_tweet_only = re.sub(r'\n', ' ', clean_tweet_only)
    clean_tweet_only = re.sub('^RT |^ | $', '', clean_tweet_only)
    clean_tweet_2 = re.sub(ProfanityRegexp, '', clean_tweet_only)
    clean_tweet_only = re.sub(
        ProfanityRegexp, '{"profanity"}', clean_tweet_only)
    clean_tweet_2 = ' '.join([st.stem(word.lower())
                              for word in clean_tweet_2.split(' ')])
    clean_tweet_2 = re.sub(' +', ' ', clean_tweet_2)
    clean_tweet_2 = re.sub('^ | $', '', clean_tweet_2)
    return (tweet, clean_tweet_2, clean_tweet_only, Hashtaglist, Userhandlelist, url_list)


def checknone(str):  # convert empty string to None
    if str == '' or str == u'':
        return None
    else:
        return str


def avrocleaning(filename1, filename2, filename3, doc_id):
    try:
        InFile = open(filename1, 'r')
        OutFile = open(filename2, 'w')
        ShemaFile = open(filename3, 'r')
    except IOError:
        print 'please check the filenames in arguments'
        return 0
    reader = DataFileReader(InFile, DatumReader())
    schema = avro.schema.parse(ShemaFile.read())
    writer = DataFileWriter(OutFile, DatumWriter(), schema)
    tweet_count = 0
    clean_tweet_count = 0
    for full_tweet_json in reader:
        tweet_count += 1
        if tweet_count % 25000 == 0:
            continue
        # if tweet_count > 100: break
        # remove leading and trailing whitespace
        try:
            # print full_tweet_json
            full_tweet = json.loads(json.dumps(full_tweet_json))
        except:
            continue
        # only select tweets in English
        if full_tweet[u'iso_language_code'] != u'en':
            # print 'not English'
            continue
        rawtweet = full_tweet[u'text']  # original tweet
        (clean_tweet, clean_tweet_2, clean_tweet_only, Hashtaglist,
         Userhandlelist, url_list) = cleanup(rawtweet)
        if clean_tweet is None:
            continue
        clean_tweet_count += 1
        full_clean_tweet = {}
        username = full_tweet[u'from_user']
        tweetID = full_tweet[u'id']
        user_id = full_tweet[u'from_user_id']
        timestamp = str(full_tweet[u'time'])  # original 'time' is of type int
        source = checknone(full_tweet[u'archivesource'])
        in_reply_to_user_id = checknone(full_tweet[u'to_user_id'])
        geocord1, geocord2 = full_tweet[
            u'geo_coordinates_0'], full_tweet[u'geo_coordinates_1']
        full_clean_tweet['tweet_id'] = tweetID.encode('ascii', 'ignore')
        unique_id = uuid.uuid3(uuid.NAMESPACE_DNS, user_id.encode('ascii', 'ignore') +
                               '_' + tweetID.encode('ascii', 'ignore'))
        full_clean_tweet['doc_id'] = doc_id + '--' + str(unique_id)
        full_clean_tweet['text_clean'] = clean_tweet_only.encode(
            'ascii', 'ignore')
        full_clean_tweet['text_clean2'] = clean_tweet_2.encode(
            'ascii', 'ignore')
        full_clean_tweet['text_original'] = rawtweet
        full_clean_tweet['created_at'] = timestamp.encode('ascii', 'ignore')
        full_clean_tweet['user_screen_name'] = username
        full_clean_tweet['user_id'] = user_id.encode('ascii', 'ignore')
        full_clean_tweet['lang'] = 'English'
        full_clean_tweet['collection'] = doc_id
        if float(geocord1) != 0.0 or float(geocord2) != 0.0:
            coordinate = '%s,%s' % (geocord1, geocord2)
            full_clean_tweet['coordinates'] = coordinate.encode(
                'ascii', 'ignore')
        if url_list != []:
            full_clean_tweet['urls'] = '|'.join(
                url_list).encode('ascii', 'ignore')
        if Userhandlelist != []:
            full_clean_tweet['user_mentions_id'] = '|'.join(
                Userhandlelist).encode('ascii', 'ignore')
        if Hashtaglist != []:
            full_clean_tweet['hashtags'] = '|'.join(
                Hashtaglist).encode('ascii', 'ignore')
        if source is not None:
            full_clean_tweet['source'] = source.encode('ascii', 'ignore')
        if in_reply_to_user_id is not None:
            full_clean_tweet['in_reply_to_user_id'] = in_reply_to_user_id.encode(
                'ascii', 'ignore')
        print full_clean_tweet
        writer.append(full_clean_tweet)
    reader.close()
    ShemaFile.close()
    writer.close()
    print filename1 + ' has been cleaned up'
    print 'total tweets: %d' % tweet_count
    print 'cleaned tweets: %d' % clean_tweet_count
    return 1


def main(argv):
    try:
        InputFile = argv[1]
        OutputFile = argv[2]
        SchemaFile = argv[3]
    except IndexError:
        print 'Please specify the tweets input avro filename, output avro filename and avro schema filename'
        return 0
    try:
        doc_id = argv[4]
    except IndexError:
        doc_id = __doc_id__
    return avrocleaning(InputFile, OutputFile, SchemaFile, doc_id)


if __name__ == '__main__':
    start_time = time.time()
    main(sys.argv)
    print("--- %s seconds ---\n\n" % (time.time() - start_time))
    sys.exit(0)
