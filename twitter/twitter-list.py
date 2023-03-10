from snscrape.modules.twitter import *
import re

def matches_any(text, expressions):
    for exp in expressions:
        pattern = re.compile(exp)
        if pattern.search(text) is not None:
            return True
    return False

def main():
    list_ids = []
    with open('list-ids.txt') as list_file:
        list_ids = list_file.read().splitlines()

    match_exp = []
    with open('match-exp.txt') as exp_file:
        match_exp = exp_file.read().splitlines()

    for list_id in list_ids:
        search = TwitterListPostsScraper(list_id).get_items()
        for tweet in search:
            text = tweet.rawContent.lower()
            if matches_any(text, match_exp):
                print({
                    "tweet": tweet.rawContent,
                    "url": tweet.url,
                })

if __name__ == '__main__':
    main()