"""
Just a regular `setup.py` file.

Author: Nikolay Lysenko
"""


import os
from setuptools import setup, find_packages


current_dir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(current_dir, 'README.md')) as f:
    long_description = f.read()

setup(
    name='otus_python_homeworks',
    version='0.1a',
    description='Solutions to homeworks for Python course hosted at Otus',
    long_description=long_description,
    url='https://github.com/Nikolay-Lysenko/otus-python-2018-02',
    author='Nikolay Lysenko',
    author_email='nikolay-lysenco@yandex.ru',
    license='MIT',
    keywords='python_courses homeworks',
    packages=find_packages(exclude=['tests', 'docs']),
    python_requires='>=2.7, <3',
    install_requires=['redis']
)
