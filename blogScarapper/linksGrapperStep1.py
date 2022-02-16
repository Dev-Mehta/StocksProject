
import requests
from bs4 import BeautifulSoup

url = 'https://www.tickertape.in/blog/category/stock-stories/'

r = requests.get(url)
soup = BeautifulSoup(r.text, 'html.parser')
links = soup.findAll('a', {'class': 'meta-item'})

histry = []
for link in links:
	histry.append(link.get('href'))
print(histry)
with open('./links.txt', 'w') as f:
	for link in histry:
		f.write(link + '\n')
