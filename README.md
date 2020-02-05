# django-watch

Simple and useful django middleware for real-time logging.

```no-highlight
https://github.com/Sobolev5/django-watch
```

# How to use it

To install run:
```no-highlight
pip install django-watch
```


Add the following lines at the end of **settings.py** file:
```python
INSTALLED_APPS = INSTALLED_APPS + ('django_watch',)
MIDDLEWARE = ( MIDDLEWARE + ('django_watch.middleware.WatchMiddleware',) )  
```


Open your development console and see the result:
```python
""" START /my_project/news/views.py => news_list: Line number 15 """
kwargs: {'news_id': '2'}
request.GET: <QueryDict: {'published_at': ['today']}>

""" END /my_project/news/views.py => news_list: Line number 15 """
sql queries time: 0.17
total time: 7.29
```

That's all.