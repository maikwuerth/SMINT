from snscrape.modules.twitter import *
import re
import json

# de-defang or refang urls, IPs, etc. 
def refang(text):
    text = text.replace("[", "")
    text = text.replace("]", "")
    text = text.replace("hxxp:", "http:")
    text = text.replace("hxxps:", "https:")
    text = text.replace("fxp:", "ftp:")
    text = text.replace("fsxp:", "fstp:")
    return text

# return all links, IPs, urls contained in tweet. except t.co
def extract_ioc(text):
    text = refang(text)
    matches = []
    # match all urls
    expression = "(?:https?:\\/\\/)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)"
    pattern = re.compile(expression)
    matches = pattern.findall(text)
    # exclude twitter links and images starting with t.co
    exclude = "\\/t\\.co\\/"
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
        print("starting list ", list_id)
        for count, tweet in enumerate(TwitterListPostsScraper(list_id).get_items()):
            if count>1000:
                break
            # match defanged
            text = tweet.rawContent.lower()
            if matches_any(text, match_exp):
                iocs = extract_ioc(text)
                output.append({
                    "iocs": iocs,
                    "tweet": tweet.rawContent,
                    "hashtags": tweet.hashtags,
                    "url": tweet.url
                })
                print({output[-1]['iocs'], output[-1]['hashtags']})
    json_output = json.dumps(output, indent=2)
    with open("output.json", "w") as out_file:
        out_file.write(json_output)

if __name__ == '__main__':
    main()