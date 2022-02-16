import os, sys, django
sys.path.append("D:\Projects\StocksProject")
sys.path.append("D:\Projects\StockBlog")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stockmarket.settings")
django.setup()

from blog.models import Post as blog_post
from posts.models import Post as post

p = post.objects.all()
for i in p:
	print(i)