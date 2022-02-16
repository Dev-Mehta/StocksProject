import os, sys
sys.path.append("D:\Projects\StocksProject")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stockmarket.settings")
import django
django.setup()
from bs4 import BeautifulSoup
from blog.models import Module, Post
import requests
with open('links.txt', 'r') as f:
	lines =  f.readlines()

for line in lines:
	url = line
	r = requests.get(url)
	soup = BeautifulSoup(r.text, 'html.parser')
	print(url)
	desc = soup.find('meta', attrs={'name':'description'})['content']
	title = soup.find('h1', class_='post-title-alt').text
	content = soup.find('div', class_='post-content description cf entry-content has-share-float content-spacious-full')
	author = soup.find('a', class_='url').get('title')
	author_url = soup.find('div', class_='abh_name').find('a').get('href')
	content.find('div', class_='abh_box').decompose()
	output = str(content)
	output += f"<p>Credits: <a href=\"{author_url}\">{author}</a> @ <a href=\"{url}\">Tickertape</a>"

	p = Post.objects.filter(title=title.strip())
	m = Module.objects.get(title='Fundamentals')
	if not p.exists():
		po = Post(title=title.strip(), content=output, module=m, description=desc)
		po.save()
		m.chapters_count += 1
		m.save()
		print("Post made")