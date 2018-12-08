import requests
import json
from bs4 import BeautifulSoup
import re
import csv
import collections
import nltk
import tltk
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report

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


# error check function (in case the number of rows are incorrect)
def error_check(tsv_file, num_of_row):
    """
    the correct number of thairath.tsv is 4 (id, headline, description, article)
    the correct number of labeled tsv is 5 (id, headline, description, article, label)
    return the id and the incorrect number of rows

    error_check('thairath.tsv', 4)
    >> 1011000 5
    """
    file = open(tsv_file)
    f = csv.reader(file, delimiter='\t')
    for line in f:
        if len(line) != num_of_row:
            print(line[0], len(line))  # print id of incorrect column


### 2. function for find articles & save as tsv ###
def find_article(keyword, label, new_tsv):
    """
    find articles that contains keyword
    save as tsv with "label" for supervised learning

    keyword: "ญีปุ่น"
    article: "ประเทศญีปุ่นจัดงาน..."
    label: "JP"
    """
    open_file = open('thairath.tsv', 'r', encoding='utf-8')
    write_file = open(new_tsv, 'a', encoding='utf-8')

    # make list of lists[id, headline, description, article] from tsv
    lines = [[id, headline, description, article]
             for id, headline, description, article in csv.reader(open_file, delimiter='\t')]

    # if article contains the keyword, add label and make new list of lists
    labeled_list = []
    for line in lines:
        description = line[2]
        article = line[3].strip('\n')
        if keyword in article or keyword in description:
            labeled_list.append(line + [label])

    # save as new tsv file
    writer = csv.writer(write_file, lineterminator='\n', delimiter='\t')
    writer.writerows(labeled_list)

    open_file.close()
    write_file.close()


### 3. function for supervised learning ###
def count_label(tsv_file):
    """
    open tsv file > tuple(id, headline, description, article, label)
    and print the number of each label

    count_tsv(country.tsv)
    >>[('JP', 3000), ('US', 2000), ('TH', 1000)]
    """
    ### open files ###
    open_file = open(tsv_file, 'r', encoding='utf-8')
    lines = [(id, headline, description, article, label)
             for id, headline, description, article, label in csv.reader(open_file, delimiter='\t')]

    ### make label list ###
    label_list = [tuple[-1] for tuple in lines]
    label_counter = collections.Counter()
    for label in label_list:
        label_counter[label] += 1
    print(label_counter.most_common())  # check the number of each label