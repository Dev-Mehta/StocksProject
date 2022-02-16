from django.db import models
from django.shortcuts import get_list_or_404, get_object_or_404, render
from django.views.generic import View

from .utils import GetRecommendation
from .models import Module, Post, Tag
# Create your views here.
class HomePage(View):
	def get(self, request, *args, **kwargs):
		modules = Module.objects.all()
		return render(self.request, 'blog/index.html', {'modules':modules})

class ModulePage(View):
	def get(self, request, *args, **kwargs):
		module = get_object_or_404(Module, slug=kwargs['module_title'])
		modules = Module.objects.all()
		posts = get_list_or_404(Post, module=module)
		print(posts)
		return render(self.request, 'blog/module.html', {'module':module, 'posts':posts, 'modules':modules})

class ModulePage(View):
	def get(self, request, *args, **kwargs):
		module = get_object_or_404(Module, slug=kwargs['module_title'])
		posts = Post.objects.filter(module=module).order_by('-upload_on')
		modules = Module.objects.all()
		return render(self.request, 'blog/module.html', {'module':module, 'posts':posts, 'modules':modules})

class PostPage(View):
	def get(self, request, *args, **kwargs):
		module = get_object_or_404(Module, slug=kwargs['module_title'])
		post = get_object_or_404(Post, slug=kwargs['post_title'])
		posts = Post.objects.filter(module=module).order_by('-upload_on') 
		modules = Module.objects.all()
		gr = GetRecommendation(post.title)
		gr.train()
		results = gr.get_result_posts()
		return render(self.request, 'blog/post.html', {'module':module, 'post':post, 'posts':results, 'modules':modules})

class TagDetail(View):
	def get(self, request, *args, **kwargs):
		tag = get_object_or_404(Tag, slug=kwargs['tag_title'])
		posts = Post.objects.filter(tags=tag).order_by('-upload_on')
		modules = Module.objects.all()
		return render(self.request, 'blog/tag_detail.html', {'posts':posts, 'modules':modules, 'tag':tag})