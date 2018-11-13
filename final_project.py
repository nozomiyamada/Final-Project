import requests
import json
from bs4 import BeautifulSoup
import re
soup = BeautifulSoup(html.text, "html.parser")

# website
matichon = requests.get('https://www.matichon.co.th/home')
thairath = requests.get('https://www.matichon.co.th/home')