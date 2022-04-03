from django.urls import path
from .views import HomePage, ModulePage, PostPage, TagDetail
from django.contrib.sitemaps import Sitemap, GenericSitemap
from .models import Post, Module, Tag
from django.contrib.sitemaps.views import sitemap
from django.urls import reverse
from django.contrib.syndication.views import Feed
info_dict = {
	'queryset': Post.objects.all(),
}
tag_dict = {
	'queryset':Tag.objects.all(),
}
class StaticViewSitemap(Sitemap):
	priority = 0.5
	changefreq = 'daily'

	def items(self):
		return ['bloghome']

	def location(self, item):
		return reverse(item)
module_dict = {
	'queryset': Module.objects.all(),
}
class PostFeed(Feed):
	title = "Blog Posts"
	link = '/feed/'
	description = 'RSS Feed for Blog'
	description_template = 'blog/post_description.html'
	def items(self):
		return Post.objects.all().order_by('-upload_on')
	def item_title(self, item):
		return item.title
	def item_description(self, item):
		return item.content
	def item_link(self, item):
		return item.get_absolute_url()

urlpatterns = [
	path('', HomePage.as_view(), name='bloghome'),
	path('module/<slug:module_title>/', ModulePage.as_view()),
	path('module/<slug:module_title>/post/<slug:post_title>/', PostPage.as_view()),
	path('tag/<slug:tag_title>/', TagDetail.as_view()),
	path('sitemap.xml/', sitemap,
		 {'sitemaps': {'blog': GenericSitemap(info_dict, priority=0.6), 'post':GenericSitemap(module_dict, priority=0.6), 'static': StaticViewSitemap, 'tags':GenericSitemap(tag_dict,priority=0.6)}}, name='django.contrib.sitemaps.views.sitemap'),
	path('feed.xml/', PostFeed()),
]