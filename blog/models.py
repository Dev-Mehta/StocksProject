from django.db import models
from django.utils.text import slugify
from taggit.managers import TaggableManager
from .apps import BlogConfig
import nltk, re, pandas as pd, numpy as np
from rake_nltk import Rake
from bs4 import BeautifulSoup
# Create your models here.
class Module(models.Model):
	title = models.CharField(max_length=255)
	chapters_count = models.IntegerField(default=0)
	description = models.TextField()
	slug = models.SlugField()
	feature_image = models.ImageField(upload_to='images/')
	color = models.CharField(max_length=25)
	upload_on = models.DateTimeField(auto_now_add=True)
	def save(self, *args, **kwargs):
		self.slug = slugify(self.title)
		super(Module,self).save(*args, **kwargs)
	def __str__(self) -> str:
		return self.title
	def get_absolute_url(self):
		return f"/blog/module/{self.slug}/"

class Tag(models.Model):
	title = models.CharField(max_length=255)
	slug = models.SlugField(default='')
	def save(self, *args, **kwargs):
		self.slug = slugify(self.title)
		super(Tag,self).save(*args, **kwargs)

	def __str__(self) -> str:
		return self.title
	
	def get_absolute_url(self):
		return f"/tag/{self.slug}/"

class Post(models.Model):
	module = models.ForeignKey(Module, on_delete=models.CASCADE)
	title = models.CharField(max_length=512)
	content = models.TextField()
	description = models.TextField()
	feature_image = models.ImageField(upload_to='images/', default='images/rubber-10.png')
	slug = models.SlugField(default='')
	quote = models.CharField(max_length=1024, blank=True, null=True)
	upload_on = models.DateTimeField(auto_now_add=True)
	tags = models.ManyToManyField('Tag', blank=True)
	def __str__(self) -> str:
		return self.title

	def save(self, *args, **kwargs):
		self.slug = slugify(self.title)
		super(Post,self).save(*args, **kwargs)
		t = create_tags(self).tags
		for tag in t.iterator():
			self.tags.add(tag)
		super(Post,self).save(*args, **kwargs)
	
	def get_absolute_url(self):
		return f"/blog/module/{self.module.slug}/post/{self.slug}/"

def create_tags(post: Post):
	title = post.title
	content = post.content
	soup = BeautifulSoup(content, 'html.parser')
	stop_words = BlogConfig.stop_words
	lemmatizer = BlogConfig.lemmatizer
	content = soup.get_text()
	content = re.sub(r'\[[0-9]*\]',' ',content) 
	content = re.sub(r'\s+',' ',content)
	title = re.sub(r'\[[0-9]*\]',' ',title)
	title = re.sub(r'\s+',' ',title)
	title = title.lower()
	clean_text = content.lower()
	regex_patterns = [r'\W',r'\d',r'\s+']
	for regex_pattern in regex_patterns:
		clean_text = re.sub(regex_pattern,' ',clean_text)
		title = re.sub(regex_pattern,' ',title)
	sentences = nltk.sent_tokenize(clean_text)
	r = Rake(stopwords=stop_words)
	word_count = {}
	r.extract_keywords_from_text(title)
	keywords = dict(r.get_ranked_phrases_with_scores())
	tags = []
	for keyword in keywords.keys():
		if int(keyword) <= 10:
			k = keywords[keyword]
			slug = slugify(k)
			key = slug.lower().replace('-', ' ').replace('/[^\w-]+/g', '')
			tags.append(key)
	tags = nltk.word_tokenize(' '.join(tags))
	for word in tags:
		if word not in stop_words:
			if word not in word_count.keys():
				word_count[word] = 1
			else:
				word_count[word] += 1
	for word in nltk.word_tokenize(clean_text):
		if word not in stop_words:
			if word not in word_count.keys():
				word_count[word] = 1
			else:
				word_count[word] += 1
	word_count_table = pd.DataFrame.from_dict(word_count, orient = 'index').rename(columns={0: 'score'})
	keywords = list(word_count_table.sort_values(by='score').tail(5).index.values)
	keywords.extend(tags)
	keywords = lemmatizer.lemmatize(' '.join(keywords)).split(' ')
	for keyword in keywords:
		slug = slugify(keyword)
		key = slug.lower().replace('-', ' ').replace('/[^\w-]+/g', '')
		t, created = Tag.objects.get_or_create(title=key)
		if created:
			t.save()
		post.tags.add(t)
	return post