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

| START GET /profiles/views.py | • todo_list_view • Line number 1934
| request.GET: <QueryDict: {'a': ['b']}>
| Exception
| TRACEBACK:
Traceback (most recent call last):
  File "handlers/base.py", line 197, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/profiles/decorators.py", line 158, in inner_decorator
    return function(request, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/main/decorators.py", line 111, in wrapper
    response = func(*args, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^
  File "/userprofiles/views.py", line 1991, in todo_list_view
    print(undef)
          ^^^^^^
NameError: name 'undef' is not defined
```

## TODO
```python
typing
__doc__ strings
```
