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
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

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
    > copy_headline(tsv, *id)
2) find_article('ญี่ปุ่น', 'JP', 'country.tsv')
2) count_label('country.tsv')
3) tokenize_headline('country.tsv', 'headline.tsv', 0, 1000)
4) ml.train('headline.tsv', 1)
4) ml.evaluate('headline_test.tsv', 1)
4) get_features(0, 100)
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

    get html, scrape with bs4, convert json to dict
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
    file = open('thairath.tsv', 'a', encoding='utf-8')  # append mode
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
def copy_headline(tsv_file, *id):  # *id > tuple of ids
    """
    some articles have only headline (no description)
    if then, copy headline to description

    incorrect data:
    line[0] = id
    line[1] = headline
    (no description)
    line[2] = article
    """
    open_file = open(tsv_file, 'r')
    write_file = open('new.tsv', 'w')
    lines = csv.reader(open_file, delimiter='\t')
    new_list = []
    for line in lines:
        if int(line[0]) in id and len(line) == 3:  # if no description
            new_line = [line[0], line[1], line[1], line[2]]  # copy headline
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
    lines = csv.reader(open_file, delimiter='\t')
    new_list = []
    for line in lines:
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
    open_file = open('thairath2.tsv', 'r', encoding='utf-8')
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
    print(label_counter)  # check the number of each label
    file.close()


### 3. functions for tokenize ###
def tokenizer(text):
    tokens = tltk.nlp.word_segment(text).split('|')
    word_list = []
    for token in tokens:
        reshaped = token.strip('<s/>')
        reshaped = reshaped.strip('<u/>')
        reshaped = reshaped.strip(' ')
        reshaped = reshaped.strip('Fail>')
        reshaped = reshaped.strip('</Fail')
        if reshaped != '':
            word_list.append(reshaped)
    return word_list


def tokenize_check(tsv_file, index):
    """
    print one article with tokenizer
    """
    with open(tsv_file) as file:
        lines = csv.reader(file, delimiter='\t')
        line = list(lines)[index]
        print(tokenizer(line[1]), '\n')
        print(tokenizer(line[2]), '\n')
        print(tokenizer(line[3]))


def tokenize_all(open_tsv, write_tsv, start_index, end_index):
    """
    read article from tsv file and save tokenized text
    tokenize_all('country.tsv', 'country_tokenized.tsv', 0, 200)
    """
    open_file = open(open_tsv, 'r', encoding='utf-8')
    write_file = open(write_tsv, 'a', encoding='utf-8')  # append mode
    lines = csv.reader(open_file, delimiter='\t')
    new_list = []
    for line in list(lines)[start_index: end_index + 1]:
        id = line[0]
        headline = '|'.join(tokenizer(line[1]))
        description = '|'.join(tokenizer(line[2]))
        article = '|'.join(tokenizer(line[3]))
        new_line = [id, headline, description, article, line[4]]
        new_list.append(new_line)

    writer = csv.writer(write_file, lineterminator='\n', delimiter='\t')
    writer.writerows(new_list)
    open_file.close()
    write_file.close()


def tokenize_headline(open_tsv, write_tsv, start_index, end_index):
    """
    tokenize only headline
    """
    open_file = open(open_tsv, 'r', encoding='utf-8')
    write_file = open(write_tsv, 'a', encoding='utf-8')  # append mode
    lines = csv.reader(open_file, delimiter='\t')
    for line in list(lines)[start_index: end_index + 1]:
        id = line[0]
        headline = '|'.join(tokenizer(line[1]))
        label = line[4]
        write_file.write(id + '\t' + headline + '\t' + label + '\n')
    open_file.close()
    write_file.close()


### 4. function for train (need instance)###
class ML:
    """
    method
    1: .train(train_tsv, index)
    2: .evaluate(test_tsv, index)
    6: .get_feature(label_index, top_k)
    """

    def __init__(self):
        self.model = LogisticRegression()
        self.dv = DictVectorizer()

    def train(self, train_tsv, index):
        """
        train with tokenized data
        split tokenized data with '|'
        index: headline...1, description...2, article...3
        """
        # make label list and feature dictionary
        file = open(train_tsv)
        lines = csv.reader(file, delimiter='\t')

        label_list = []
        feat_dic_list = []
        for line in lines:
            word_list = line[index].split('|')
            feat_dic = {word: 1 for word in word_list if word != '' and word[0].isalpha()}
            feat_dic['LENGTH'] = len(word_list)  # length of sentence
            feat_dic_list.append(feat_dic)
            label_list.append(line[-1])

        # sparse matrix & train
        sparse_feature_matrix = self.dv.fit_transform(feat_dic_list)
        self.model.fit(sparse_feature_matrix, np.array(label_list))

    def get_feature(self, label_index, top_k):
        # get features from index
        parameter_matrix = self.model.coef_
        top_features = parameter_matrix.argsort()[:, -(top_k) - 1:-1]
        label_top_features = [self.dv.get_feature_names()[x] for x
                              in top_features[label_index]]
        label_top_features.reverse()
        print(label_top_features)

    def evaluate(self, test_tsv, index):
        file = open(test_tsv)
        lines = csv.reader(file, delimiter='\t')

        label_list = []
        feat_dic_list = []
        for line in lines:
            word_list = line[index].split('|')
            feat_dic = {word: 1 for word in word_list if word != '' and word[0].isalpha()}
            feat_dic['LENGTH'] = len(word_list)  # length of sentence
            feat_dic_list.append(feat_dic)
            label_list.append(line[-1])

        self.label_list = label_list
        # sparse matrix & test
        sparse_feature_matrix = self.dv.transform(feat_dic_list)
        self.result_list = self.model.predict(sparse_feature_matrix)

        # accuracy
        accuracy = accuracy_score(self.label_list, self.result_list)
        print("Accuracy")
        print(accuracy)

        # confusion matrix
        matrix = confusion_matrix(self.label_list, self.result_list)
        print("\nConfusion Matrix")
        print(matrix)

        # Precision, Recall, F score
        report = classification_report(self.label_list, self.result_list)
        print("\nReport")
        print(report)


ml = ML()