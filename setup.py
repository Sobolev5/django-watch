import os
import sys
import setuptools

__author__ = 'Sobolev Andrey <email.asobolev@gmail.com>'
__version__ = '0.1.3'

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='django-watch',
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
    python_requires='>=3.4',
)