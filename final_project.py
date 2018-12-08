import requests
import json
from bs4 import BeautifulSoup
import re
import nltk
import tltk
soup = BeautifulSoup(html.text, "html.parser")

"""
process of this program
1. get articles and headlines from Thairath (as many as possible & regardless of content for future works)
2. find articles that contains keyword (in this project, use 'countries')
3. supervised training with sk-learn
4. find words and metaphors that uniquely indicate the country
"""


### 1. function for scraping ###
url = 'https://www.thairath.co.th/content/'
file = open('thairath.tsv', 'a')
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
    for id in range(start_id, start_id + number):
        response = requests.get(url + str(id)) # get html
        if response.status_code == 200: # if 404 pass
            soup = BeautifulSoup(response.text, "html.parser") # get text
            html = soup.find_all('script', type="application/ld+json") # find more than 2 tags <script>
            dict = json.loads(html.text[-1]) # convert final one from json into dict

            headline = return_str(dict['headline'])
            description = return_str(dict['description'])
            article = return_str(dict['articleBody'])

            file.write(str(id) + '\t' + headline + '\t' + description
                       + '\t' + article + '\n') # save as tsv
    file.close()
