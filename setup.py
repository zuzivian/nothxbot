# -*- coding: utf-8 -*-

# Learn more: https://github.com/zuzivian/nothxbot

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='sample',
    version='0.0.1',
    description='A Telegram implementation of the card game, No Thanks',
    long_description=readme,
    author='Nathaniel Wong',
    author_email='rubikcode@gmail.com',
    url='https://github.com/zuzivian/nothxbot',
    license=license,
    packages=find_packages()
)