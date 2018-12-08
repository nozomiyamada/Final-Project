import requests
import json
from bs4 import BeautifulSoup
import re
import csv

# import nltk
# import tltk

"""
process of this program
1. get articles and headlines from Thairath
    (as many as possible & regardless of content for future works)
2. find articles that contains keyword (in this project, use 'countries')
3. supervised training with sk-learn
4. find words and metaphors that uniquely indicate the country
"""

### 1. function for scraping ###
url = 'https://www.thairath.co.th/content/'
"""
all contents of Thairath are https://www.thairath.co.th/content/******
"""


def text_trim(text):
    """
    trim scraped text with .replace
    """
    text = text.replace('\r', '')
    text = text.replace('\n', ' ')
    text = text.replace('\t', ' ')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&ndash;', '–')
    text = text.replace('&amp;', '&')
    text = text.replace('&lsquo;', '‘')
    text = text.replace('&rsquo;', '’')
    text = text.replace('&ldquo;', '“')
    text = text.replace('&rdquo;', '”')
    return text


def return_str(text):
    """
    return original text if any
    return '' if None
    (sometimes there is no content in certain keys of json)
    """
    if text == None:
        return ''
    else:
        return text_trim(text)


def scrape(start_id, number):
    """
    specify content id and the maximum number of request.get

    scrape(1000000, 100)
    >> save id, headline, description, article as tsv file

    get html as json and convert to dict
    html structure is:

    <script type = "application/ld+json" async = "" class = "next-head">{
    "headline": "..."
	"description": "...."
    "articleBody": "....."
    .....
    }</script>

    ##note: all articles have the same structure "<script>...</script>" more than 2 times
    but always final one is the real content
    """
    file = open('thairath.tsv', 'a', encoding='utf-8')
    for id in range(start_id, start_id + number):
        response = requests.get(url + str(id))  # get html
        if response.status_code == 200:  # if 404 pass
            soup = BeautifulSoup(response.text, "html.parser")  # get text
            content_list = soup.find_all('script', type="application/ld+json")  # find more than 2 tags <script>
            dict = json.loads(content_list[-1].text)  # convert final one from json into dict

            headline = return_str(dict['headline'])
            description = return_str(dict['description'])
            article = return_str(dict['articleBody'])

            file.write(str(id) + '\t' + headline + '\t' + description
                       + '\t' + article + '\n')  # save as tsv
    file.close()


### 2. function for find articles & save as tsv ###
def find_article(keyword, label, new_tsv):
    open_file = open('thairath.tsv', 'r', encoding='utf-8')
    write_file = open(new_tsv, 'a', encoding='utf-8')

    lines = [(id, headline, description, article)
             for id, headline, description, article in csv.reader(open_file, delimiter='\t')]
    for line in lines:
        id = line[0]
        headline = line[1]
        description = line[2]
        article = line[3].strip('\n')
        if keyword in article or keyword in description:
            write_file.write(str(id) + '\t' + headline + '\t' + description
                             + '\t' + article + '\t' + label + '\n')  # save as tsv

    open_file.close()
    write_file.close()