import time


def unwrap(func):
    while hasattr(func, '__wrapped__'):
        func = func.__wrapped__
    return func


class WatchMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response
        self.BLACK = "\033[0;30m"
        self.RED = "\033[0;31m"
        self.GREEN = "\033[0;32m"
        self.BROWN = "\033[0;33m"
        self.BLUE = "\033[0;34m"
        self.PURPLE = "\033[0;35m"
        self.CYAN = "\033[0;36m"
        self.LIGHT_GRAY = "\033[0;37m"
        self.DARK_GRAY = "\033[1;30m"
        self.LIGHT_RED = "\033[1;31m"
        self.LIGHT_GREEN = "\033[1;32m"
        self.YELLOW = "\033[1;33m"
        self.LIGHT_BLUE = "\033[1;34m"
        self.LIGHT_PURPLE = "\033[1;35m"
        self.LIGHT_CYAN = "\033[1;36m"
        self.LIGHT_WHITE = "\033[1;37m"
        self.BOLD = "\033[1m"
        self.FAINT = "\033[2m"
        self.ITALIC = "\033[3m"
        self.UNDERLINE = "\033[4m"
        self.BLINK = "\033[5m"
        self.NEGATIVE = "\033[7m"
        self.CROSSED = "\033[9m"
        self.END = "\033[0m"

    def __call__(self, request):
        response = None

        time_start = time.process_time()      
        response = self.get_response(request)

        if hasattr(response, 'status_code') and response.status_code in [200, 201] and hasattr(request, 'process_stdout_end') and request.process_stdout_end:
            process_stdout_end = request.process_stdout_end            
            process_stdout_end += f'\n{self.YELLOW}Total time :: {round((time.process_time() - time_start), 2)}s{self.END}'        
            print(process_stdout_end)      
        return response


    def process_view(self, request, func, args, kwargs):                 
        func = unwrap(func)   
        if hasattr(func, '__code__'):
            process_stdout_start = f'\n{self.GREEN}START {func.__code__.co_filename} :: {self.END}{self.RED}{self.BOLD}{func.__name__}{self.END}{self.END} {self.GREEN}::{self.END} {self.LIGHT_BLUE}{self.ITALIC}Line number {func.__code__.co_firstlineno} {self.END}{self.END}'
            request.process_stdout_end = f'\n{self.YELLOW}END {func.__code__.co_filename} :: {self.END}{self.RED}{self.BOLD}{func.__name__}{self.END}{self.END} {self.YELLOW}:: Line number {func.__code__.co_firstlineno} {self.END}'
            if args: 
                print_part = f'args: {args}'
                if len(print_part) > 200:
                    process_stdout_start += f'\n{self.PURPLE}%s ...{self.END}' % print_part[:200]
                else:
                    process_stdout_start += f'\n{self.PURPLE}%s{self.END}' % print_part
            if kwargs: 
                print_part = f'kwargs: {kwargs}'
                if len(print_part) > 200:
                    process_stdout_start += f'\n{self.PURPLE}%s ...{self.END}' % print_part[:200]
                else:
                    process_stdout_start += f'\n{self.PURPLE}%s{self.END}' % print_part
            if request.GET:
                print_part = f'request.GET: {request.GET}'
                if len(print_part) > 200:
                    process_stdout_start += f'\n{self.PURPLE}%s ...{self.END}' % print_part[:200]
                else:
                    process_stdout_start += f'\n{self.PURPLE}%s{self.END}' % print_part
            if request.POST: 
                print_part = f'request.POST: {request.POST}'
                if len(print_part) > 200:
                    process_stdout_start += f'\n{self.PURPLE}%s ...{self.END}' % print_part[:200]
                else:
                    process_stdout_start += f'\n{self.PURPLE}%s{self.END}' % print_part             
            print(process_stdout_start) 

        return None    
    

    def process_exception(self, request, exception):
        if hasattr(request, 'process_stdout_end') and request.process_stdout_end: 
            exception_stdout = request.process_stdout_end   
            exception_stdout += f'\n{self.RED}{self.BOLD}Exception :: {exception}{self.END}{self.END}'
            print(exception_stdout)
 