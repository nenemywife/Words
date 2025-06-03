import requests
from bs4 import BeautifulSoup

url = "https://dictionary.cambridge.org/zht/%E8%A9%9E%E5%85%B8/%E8%8B%B1%E8%AA%9E-%E6%BC%A2%E8%AA%9E-%E7%B9%81%E9%AB%94/like"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}
web = requests.get(url, headers=headers)
soup = BeautifulSoup(web.text, "html5lib")

divs = soup.find_all('div', {"class":"def-body ddef_b"})

for div in divs:
    d = div.find("span")
    print(d.text)