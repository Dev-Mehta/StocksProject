from .models import Post
import re,math
from collections import Counter
from bs4 import BeautifulSoup

class GetRecommendation:
	WORD = re.compile(r"\w+")
	post = None
	result = {}
	def __init__(self, title):
		self.post = Post.objects.get(title=title)

	def get_cosine(self, vec1, vec2):
		interesection = set(vec1.keys()) & set(vec2.keys())
		numerator = sum([vec1[x] * vec2[x] for x in interesection])
		sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
		sum2 = sum([vec2[x] ** 2 for x in list(vec1.keys())])
		denominator = math.sqrt(sum1) * math.sqrt(sum2)
		if not denominator:
			return 0.0
		return float(numerator) / denominator
	def text_to_vector(self, text):
		words = self.WORD.findall(text)
		return Counter(words)
	def train(self):
		self.result.clear()
		tags = self.post.tags.all()[:3]
		for tag in tags:
			other_posts = Post.objects.filter(tags__title=tag.title)
			for other_post in other_posts:
				X_content = BeautifulSoup(self.post.content, 'html.parser').get_text()
				Y_content = BeautifulSoup(other_post.content, 'html.parser').get_text()
				X_content = self.text_to_vector(X_content)
				Y_content = self.text_to_vector(Y_content)
				cosine = self.get_cosine(X_content, Y_content)
				cosine2 = cosine + self.get_cosine(self.text_to_vector(self.post.title), self.text_to_vector(other_post.title))
				self.result[other_post.title] = cosine2
		self.result = dict(sorted(self.result.items(), key=lambda item: item[1], reverse=True))
	
	def get_result_posts(self):
		titles = list(self.result.keys())[:10]
		posts = []
		for t in titles:
			posts.append(Post.objects.get(title=t))
		return posts