# django-watch

Light and useful django middleware for real-time logging in development.

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
if DEBUG:
    INSTALLED_APPS = INSTALLED_APPS + ('django_watch',)
    MIDDLEWARE = ( MIDDLEWARE + ('django_watch.middleware.WatchMiddleware',) )  
```


Open your development console and see the result:
```python

░░ GET main/views.py  • profile • Line number 191

░░ GET main/views.py  • profile [  OK  ] • STATUS 200 • Total time • 8.92s
```


