# -*- coding: utf-8 -*-
"""
Created on Mon Aug 27 08:44:12 2018

@author: bbranchf

this is a setup script for the FamilySearch class to hopefully reduce the load
time of the programs that use the module we created
"""

from setuptools import setup, find_packages

setup(name = 'FamilySearch',
      version = '1.0',
      description = 'Python Distribution Utilities',
      author = 'The Record Linking Lab',
      author_email = 'record_linking_lab@byu.edu',
      url = 'http://rll.byu.edu/home.html',
      description = ('A collection of functions that interact with '
                 'familysearch.org to work with batches of information'),
      packages = ['FamilySearch1'],
      )


