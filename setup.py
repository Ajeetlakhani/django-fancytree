#!/usr/bin/env python

from setuptools import setup, find_packages
import fancytree
import os

setup(name='django-mptt-autocomplete',
      version=fancytree.__version__,
      description='Django mppt widget that uses Fancytree to search and display tree data',
      author='Ajeet Lakhani',
      author_email='ajeet.lakhani@hotmail.com',
      url='https://github.com/xrmx/django-fancytree',
      packages=find_packages(),
      keywords=['django', 'fancytree', 'mptt', 'tree'],
      classifiers=[
          'Programming Language :: Python',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Environment :: Web Environment',
          'Framework :: Django',
          'Topic :: Software Development :: Libraries :: Application Frameworks',
      ],
      long_description=open(
          os.path.join(os.path.dirname(__file__), 'README.rst'),
      ).read().strip(),
      install_requires=[
          'Django',
          'django-mptt',
      ],
      include_package_data=True
)
