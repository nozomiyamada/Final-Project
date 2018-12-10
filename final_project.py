import requests
import json
from bs4 import BeautifulSoup
import re
import csv
import numpy as np
import collections

import nltk
import tltk

from sklearn.linear_model import LogisticRegression

model = LogisticRegression()

from sklearn.feature_extraction import DictVectorizer

dv = DictVectorizer()

from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report

"""
process of this program
1) get articles and headlines from Thairath
    (as many as possible & regardless of content for future works)
2) find articles that contains keyword (in this project, use 'countries')
3) supervised training with sk-learn
4) find words and metaphors that uniquely indicate the country

all process
1) scrape(130000, 1000)
1) error_check('thairath.tsv')
    > if any, print_content(id)
    > copy_headline(tsv, id)
2) find_article('ญี่ปุ่น', 'JP', 'country.tsv')
3) count_label('country.tsv')
3) tokenize_check(tsv, index)
3) train('country.tsv', 2)
3) get_features(2, 20)
"""

### 1. function for scraping ###
url = 'https://www.thairath.co.th/content/'
"""
all contents of Thairath are https://www.thairath.co.th/content/******
"""


def text_trim(text):
    """
    trim scraped text from html
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


# error check 1 (in case the number of rows are incorrect)
def error_check(tsv_file, num_of_row):
    """
    the correct number of thairath.tsv is 4 (id, headline, description, article)
    the correct number of labeled tsv is 5 (id, headline, description, article, label)
    return the id and the incorrect number of rows

    error_check('thairath.tsv', 4)
    >> 1011000 5
    """
    with open(tsv_file) as file:
        lines = csv.reader(file, delimiter='\t')
        for line in lines:
            if len(line) != num_of_row:
                print(line[0], len(line))  # print id of incorrect column


# error check 2 (specify how incorrect one incorrect)
def print_content(tsv_file, id):
    """
    print one article from id in order to check

    print_content('thairath.tsv', 1200000)
    >> 1200000
    >> headline
    >> description
    >> article
    """
    with open(tsv_file) as file:
        lines = csv.reader(file, delimiter='\t')
        for line in lines:
            if line[0] == str(id):
                for i in range(len(line)):
                    print(i, line[i])
                    print('--------------------------------------')


# error check 3 (reshape tsv)
def copy_headline(tsv_file, id):
    """
    some articles have only headline (no description)
    if then, copy headline to description

    incorrect data:
    line[0] = id
    line[1] = headline
    line[2] = article
    """
    open_file = open(tsv_file)
    write_file = open('new.tsv', 'w')
    lines = csv.reader(open_file, delimiter='\t')
    new_list = []
    for line in lines:
        if line[0] == str(id) and len(line) == 3:
            new_line = [line[0], line[1], line[1], line[2]]
            new_list.append(new_line)
        else:
            new_list.append(line)

    # save as new tsv file
    writer = csv.writer(write_file, lineterminator='\n', delimiter='\t')
    writer.writerows(new_list)
    open_file.close()
    write_file.close()


# error check 4 (delete article)
def delete(tsv_file, id):
    """
    delete one line with specifying ID
    """
    open_file = open(tsv_file)
    write_file = open('new.tsv', 'w')
    f = csv.reader(open_file, delimiter='\t')
    new_list = []
    for line in f:
        if line[0] == str(id):
            pass
        else:
            new_list.append(line)

    # save as new tsv file
    writer = csv.writer(write_file, lineterminator='\n', delimiter='\t')
    writer.writerows(new_list)
    open_file.close()
    write_file.close()


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
    write_file = open(new_tsv, 'a', encoding='utf-8')  # append mode
    lines = csv.reader(open_file, delimiter='\t')

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
    file = open(tsv_file, 'r', encoding='utf-8')
    lines = csv.reader(file, delimiter='\t')

    ### make label list ###
    label_list = [line[-1] for line in lines]
    label_counter = collections.Counter()
    for label in label_list:
        label_counter[label] += 1
    print(label_counter.most_common())  # check the number of each label
    file.close()


# functions for train
def tokenizer(text):
    tokens = tltk.nlp.word_segment(text).split('|')
    word_list = []
    for token in tokens:
        reshaped = token.strip('<s/>')
        reshaped = reshaped.strip('<u/>')
        if reshaped != ' ':
            word_list.append(reshaped)
    return word_list


def tokenize_check(tsv_file, index):
    """
    print one article with tokenizer
    """
    with open(tsv_file) as file:
        f = csv.reader(file, delimiter='\t')
        line = list(f)[index - 1]
        print(tokenizer(line[-1]))


def train(tsv_file, index):
    """
    train with
    headline ... index = 1
    description ... index = 2  # most appropriate
    article ... index = 3 # toooooooo long
    """
    # make label list and feature dictionary
    file = open(tsv_file)
    lines = csv.reader(file, delimiter='\t')

    label_list = []
    feat_dic_list = []
    for line in lines:
        word_list = tokenizer(line[index])  # ex. line[1] = headline
        feat_dic = {word: 1 for word in word_list if not word[0].isdigit()}
        feat_dic['LENGTH'] = len(word_list)  # length of sentence
        feat_dic_list.append(feat_dic)
        label_list.append(line[-1])

    # sparse matrix & train
    sparse_feature_matrix = dv.fit_transform(feat_dic_list)
    model.fit(sparse_feature_matrix, np.array(label_list))


def get_features(label_index, top_k):
    # get features from index
    parameter_matrix = model.coef_
    top_features = parameter_matrix.argsort()[:, -(top_k) - 1:-1]
    label_top_features = [dv.get_feature_names()[x] for x
                          in top_features[label_index]]
    label_top_features.reverse()
    print(label_top_features)
