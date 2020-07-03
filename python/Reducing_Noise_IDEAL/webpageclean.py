#!/usr/bin/env python
# coding: utf-8
'''
Codes for cleaning up webpages locally
Author: X.W, P.C
'''


import sys
from readability.readability import Document
import re
from bs4 import BeautifulSoup
import avro
import avro.schema
from avro.datafile import DataFileWriter
from avro.io import DatumWriter
from nltk.stem.lancaster import LancasterStemmer
from urlparse import urlparse
from langdetect import detect_langs
import uuid
import time

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


def cleanblankspaces(clean_content0):
    clean_content = clean_content0
    clean_content = re.sub(' . ', '. ', clean_content)
    clean_content = re.sub(' (,|;) ', ', ', clean_content)
    clean_content = re.sub(' +', ' ', clean_content)
    clean_content = re.sub('^ | $', '', clean_content)
    return clean_content


def webcontentcleanup(content):
    UrlRegexp = r'(?P<url>https?://[a-zA-Z0-9\./-]+)'
    ProfanityRegexp = re.compile(
        r'(?<=^|(?<=[^a-zA-Z0-9-\.]))(' + '|'.join(__profanity_words__) + r')(?=$|\W)', re.IGNORECASE)
    url_list = re.findall(UrlRegexp, content)
    for url in url_list:
        content = content.replace(url, '')
    clean_content_only = ' '.join(
        [word for word in content.split(' ') if word.lower() not in __stop_word__])
    clean_content_2 = re.sub(ProfanityRegexp, '', clean_content_only)
    clean_content_only = re.sub(ProfanityRegexp, '{"profanity"}', clean_content_only)
    clean_content_2 = ' '.join([st.stem(word)
                                for word in clean_content_2.split(' ')])
    clean_content_only = cleanblankspaces(clean_content_only)
    clean_content_2 = re.sub(r'([^\s\w]|_)+', '', clean_content_2)
    clean_content_2 = cleanblankspaces(clean_content_2)
    url_list_str = '|'.join(url_list)
    return (clean_content_only, clean_content_2, url_list_str)


def avrocleaning(filename1, filename2, filename3, doc_id):
    try:
        InFile = open(filename1, 'r')
        OutFile = open(filename2, 'w')
        SchemaFile = open(filename3, 'r')
        fp = open('test.dat', 'w')
    except IOError:
        print 'please check the filenames in arguments'
        return 0
    raw_text_all = InFile.read().decode('utf8')
    InFile.close()
    schema = avro.schema.parse(SchemaFile.read())
    writer = DataFileWriter(OutFile, DatumWriter(), schema)
    regex_raw_webpage = re.compile(
        'url:.*?contentType:.*?Content:.*?Version: -1', re.DOTALL)
    regex_webpage = re.compile('Content:.*Version: -1', re.DOTALL)
    regex_url = re.compile(r'(?<=url: )http.*')
    regex_contentType = re.compile(r'(?<=contentType: ).*')
    regex_rubbish = re.compile('http.*Version: -1')
    webpages = re.findall(
        regex_raw_webpage, raw_text_all + '\nhttp:TO_FIND_THE_LAST_WBBPAGE_Version: -1')
    clean_webpage_count = 0
    html_file_count = 0
    contentTypeAll = {}
    languageAll = {}
    for raw_text in webpages:
        url = re.findall(regex_url, raw_text)[0].strip()
        contentType = re.findall(regex_contentType, raw_text)[0].strip()
        if contentType not in contentTypeAll:
            contentTypeAll[contentType] = 1
        else:
            contentTypeAll[contentType] += 1
        if contentType.find('html') < 0:
            continue
        html_file_count += 1
        raw_text = re.findall(regex_webpage, raw_text)[0]
        raw_text = re.sub(regex_rubbish, '', raw_text)
        readable_article = Document(raw_text).summary()
        readable_title = Document(raw_text).short_title()
        readable_title = ''.join(
            [i if ord(i) < 128 else ' ' for i in readable_title])
        # url = ''.join([i if ord(i) < 128 for i in url])
        url = url.decode("utf8")
        readable_title = re.sub(' +', ' ', readable_title)
        soup = BeautifulSoup(readable_article)
        texts = soup.findAll(text=True)
        all_text = ' '.join(texts).strip()
        try:
            lan = str(detect_langs(all_text)[0]).split(':')[0]
        except:
            continue
        if lan not in languageAll:
            languageAll[lan] = 1
        else:
            languageAll[lan] += 1
        if lan != 'en':
            continue
        all_text = all_text.replace('\r\n', ' ')
        all_text = all_text.replace('\n', ' ')
        all_text = all_text.replace('\t', ' ')
        all_text = ''.join([i if ord(i) < 128 else ' ' for i in all_text])
        all_text = re.sub(' +', ' ', all_text)
        (clean_content_only, clean_content_2, url_list_str) = webcontentcleanup(all_text)
        # print clean_content_2
        domain = '{uri.netloc}'.format(uri=urlparse(url))
        webpage_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, url.encode('ascii', 'ignore')))
        webpage_json = {}
        webpage_json["doc_id"] = doc_id + '--webpage--' + webpage_id
        webpage_json["text_clean"] = clean_content_only
        webpage_json["text_original"] = raw_text
        webpage_json["title"] = readable_title
        webpage_json["text_clean2"] = clean_content_2
        webpage_json["collection"] = doc_id
        webpage_json["content_type"] = 'html'
        webpage_json["urls"] = url_list_str
        webpage_json["domain"] = domain
        webpage_json["url"] = url
        writer.append(webpage_json)
        clean_webpage_count += 1
        fp.write("%s\n%s\n\n%s\n\n\n\n\n" %
                 (doc_id + '--webpage--' + webpage_id, url, clean_content_only))
    fp.close()
    SchemaFile.close()
    writer.close()
    print filename1 + ' has been cleaned up'
    print 'Total webpages: %d' % len(webpages)
    print 'Cleaned webpages: %d' % clean_webpage_count
    print 'Percentage cleaned: %.3f' % (100.0*clean_webpage_count/len(webpages))
    print 'HTML webpages: %d' % html_file_count
    print 'Non-English webpages: %d' % (html_file_count-clean_webpage_count)
    print 'Content Type Statistics: ', contentTypeAll
    print 'Language Statitics: ', languageAll
    return 1


def main(argv):
    try:
        InputFile = argv[1]
        OutputFile = argv[2]
        SchemaFile = argv[3]
    except IndexError:
        print 'Please specify the webpage input avro filename, output avro filename and avro schema filename'
        return 0
    try:
        doc_id = argv[4]
    except IndexError:
        doc_id = __doc_id__
    return avrocleaning(InputFile, OutputFile, SchemaFile, doc_id)

if __name__ == '__main__':
    start_time = time.time()
    main(sys.argv)
    print("--- %s seconds ---\n\n\n" % (time.time() - start_time))
    sys.exit(0)
