from snscrape.modules.twitter import *
import re
from pymisp import ExpandedPyMISP, PyMISP, MISPEvent, MISPAttribute, MISPObject
from datetime import datetime, date, timedelta
import urllib3
import json

# add your own MISP instance and creds to keys.py
import keys

# DEBUG
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_attribute_type(attribute):
    pattern = re.compile('^(\d{1,3}\.){3}\d{1,3}$')
    if pattern.match(attribute):
        return 'ioc-ip'
    pattern = re.compile('^(http|ftp)')
    if pattern.match(attribute):
        return 'ioc-url'
    else:
        return 'ioc-domain'

# de-defang or refang urls, IPs, etc.
def refang(text):
    text = text.replace('[', '')
    text = text.replace(']', '')
    text = text.replace('hxxp:', 'http:')
    text = text.replace('hxxps:', 'https:')
    text = text.replace('fxp:', 'ftp:')
    text = text.replace('fsxp:', 'fstp:')
    return text

# return all links, IPs, urls contained in tweet. except t.co
def extract_ioc(text):
    text = refang(text)
    matches = []
    # match all urls
    expression = '(?:https?:\\/\\/)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)'
    pattern = re.compile(expression)
    matches = pattern.findall(text)
    # exclude twitter links and images starting with t.co
    exclude = '\\/t\\.co\\/'
    pattern = re.compile(exclude)
    matches = [m for m in matches if not pattern.search(m)]
    return matches

# fast match any defanged urls, IPs, etc.
def matches_any(text, expressions):
    for exp in expressions:
        pattern = re.compile(exp)
        if pattern.search(text):
            return True
    return False

def main():
    today = date.today()
    yesterday = today - timedelta(days=1)

    # read ids of twitter lists to scrape
    list_ids = []
    with open('list-ids.txt') as list_file:
        list_ids = list_file.read().splitlines()

    # read regular expressions to match defanged urls
    match_exp = []
    with open('match-exp.txt') as exp_file:
        match_exp = exp_file.read().splitlines()

    output = []
    # scrape 1000 tweets list by list
    for list_id in list_ids:
        print('starting list ', list_id)
        for count, tweet in enumerate(TwitterListPostsScraper(list_id).get_items()):
            if count>1000:
                break
            # match defanged and tweets from either today or yesterday
            text = tweet.rawContent.lower()
            if matches_any(text, match_exp) and (tweet.date.date() == yesterday or tweet.date.date() == today):
                iocs = extract_ioc(text)
                output.append({
                    'iocs': iocs,
                    'text': tweet.rawContent,
                    'hashtags': tweet.hashtags,
                    'url': tweet.url,
                    'date': tweet.date
                })
                print(iocs)

    # filter output
    tmp = []
    for i in range(len(output)):
        # deduplicate
        if output[i] not in output[i + 1:]:
            tmp.append(output[i])

    output = tmp

    # exit if we dont have any results
    if len(output) == 0:
        exit()

    # add results to MISP
    pymisp = PyMISP(keys.misp_url, keys.misp_key, False, 'json')

    # create todays MISP Event
    misp_event = MISPEvent()
    misp_event.info = f'Twitter OSINT - {yesterday}'
    misp_event.add_tag('type:OSINT')

    # add tweets to Event
    for tweet in output:
        search_result = pymisp.search(controller='attributes', return_format='json', value=tweet['url'], type_attribute='link')
        # object already exist
        print(tweet['url'])
        print(search_result)
        if search_result.get('Attribute', []):
            continue
        misp_object = MISPObject('osint-tweet', misp_objects_path_custom='misp-objects')
        misp_object.add_attribute('tweet-link', tweet['url'])
        misp_object.add_attribute('tweet-text', tweet['text'])
        misp_object.add_attribute('tweet-date', tweet['date'])
        if 'hashtags' in tweet:
            for hashtag in tweet['hashtags']:
                misp_object.add_attribute('tweet-hashtag', hashtag)
        for ioc in tweet['iocs']:
            misp_object.add_attribute(get_attribute_type(ioc), ioc)
        misp_event.add_object(misp_object)

    # push MISPEvent
    pymisp.add_event(misp_event)


if __name__ == '__main__':
    main()