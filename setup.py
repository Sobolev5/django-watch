import os
import sys
import setuptools

__author__ = 'Sobolev Andrey <email.asobolev@gmail.com>'
__version__ = '0.1.0'

with open("README.md", "r") as fh:
    long_description = fh.read()

if sys.argv[-1] == 'publish':
    os.system('python setup.py django_watch upload')
    sys.exit()

setuptools.setup(
    name='django-watch-Sobolev5',
    version=__version__,
    install_requires=['termcolor>=1.1.0', 'django>=1.11'],
    author='Sobolev Andrey',
    author_email='email.asobolev@gmail.com',
    description='A set of tools for simple load testing and real-time logging.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)