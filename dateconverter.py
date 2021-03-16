# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 10:23:15 2019

@author: bbranchf
"""

import datetime
import csv
import pandas as pd
import os
import re

os.chdir(r'R:\JoePriceResearch\Python\all_code\FamilySearch1\test_data')
infile = 'find_test_catholic.csv'
outfile = 'find_test_out.csv'

print(datetime.datetime.strptime('20-Nov-2002', '%d-%b-%Y').strftime('%Y-%m-%d'))

with open(outfile, 'a') as csvFile:
    writer = csv.writer(csvFile)
csvFile.close()

# Read in the input file.
varList = ['givenName', 'surname', 'sex', 'birthLikeDate', 'birthLikePlace',
           'fatherGvienName', 'fatherSurname', 'motherGivenName']
df = pd.read_csv(infile)
print(datetime.datetime.strptime(df.loc[1579,3], '%d %b %Y'))

print(df)
for index, row in df.iterrows():
    if row['birthLikeDate'].isna():
        continue
    elif re.match(r"^\d{8}$", row['birthLikeDate']):
        print(datetime.strptime(row['birthLikeDate'],'%Y%m%d'))
    elif re.match(r"^\d{1,2}/", row['birthLikeDate']):
        print(datetime.strptime(row['birthLikeDate'],'%m/%d/%Y'))
    elif re.match(r"^[a-z]{3}", row['birthLikeDate'], re.IGNORECASE):
        print(datetime.strptime(row['birthLikeDate'],'%b %d %Y'))
    elif re.match(r"^\d{1,2} [a-z]{3}", row['birthLikeDate'], re.IGNORECASE):
        print(datetime.strptime(row['birthLikeDate'],'%d %b %Y'))
    else:
        print(row['birthLikeDate'])


