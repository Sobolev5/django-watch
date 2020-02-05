# django-watch

A set of tools for simple load testing and real-time logging.

# How to use it

To install run:
```no-highlight
pip install django-watch
```

Add the following lines at the end of **settings.py** file
```python
INSTALLED_APPS = INSTALLED_APPS + ('django_watch',)
MIDDLEWARE = ( MIDDLEWARE + ('django_watch.middleware.WatchMiddleware',) )  
```
That's all.