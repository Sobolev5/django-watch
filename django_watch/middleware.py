import time
from termcolor import cprint
from settings import DEBUG
from django.db import connection


def unwrap(func):
    while hasattr(func, '__wrapped__'):
        func = func.__wrapped__
    return func

class WatchMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response
        
    def __call__(self, request):
        response = None

        time_start = time.clock()      
        response = self.get_response(request)

        if hasattr(response, 'status_code') and response.status_code == 200 and hasattr(request, 'django_watch_process_stdout') and request.django_watch_process_stdout:
            response_stdout = request.django_watch_process_stdout            
            if DEBUG and connection.queries: 
                queries_time = sum([float(q['time']) for q in connection.queries])
                response_stdout += f'\nsql queries time: {round(queries_time, 2)}'
            response_stdout += f'\ntotal time: {round((time.clock() - time_start), 2)}\n\n'        
            cprint(response_stdout, 'green')         
        return response


    def process_view(self, request, func, args, kwargs):                 
        func = unwrap(func)      
        if hasattr(func, '__code__'):
            process_stdout = f'\n""" START {func.__code__.co_filename} => {func.__name__}: Line number {func.__code__.co_firstlineno}"""'
            request.django_watch_process_stdout = process_stdout.replace('START','END')[:]
            if args: process_stdout += f'\nargs: {args}='
            if kwargs: process_stdout += f'\nkwargs: {kwargs}' 
            if request.GET: process_stdout += f'\nrequest.GET: {request.GET}'
            if request.POST: process_stdout += f'\nrequest.POST: {request.POST}'
            cprint(process_stdout, 'yellow') 
        return None    
    

    def process_exception(self, request, exception):
        exception_stdout = request.django_watch_process_stdout   
        exception_stdout += f'\n exception: {exception}' 
        cprint(exception_stdout, 'red')  