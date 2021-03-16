# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 10:44:51 2019

@author: winwardn
"""

import sys
#sys.path.append(r'V:\anaconda3\envs\record_linking\Lib\site-packages')
import os
import pandas as pd
from contextlib import contextmanager
import time

@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout

sys.path.append(r'R:\JoePriceResearch\Python\all_code')
from FamilySearch1 import FamilySearch

def ScrapeIslands(self, backUpFile='backUpFile.csv'):  
    inputFile = self.infile
    
    if inputFile[-3:] == 'csv':
        remainingPids = pd.read_csv(inputFile).filter(['pid'])
    elif inputFile[-3:] == 'dta':
        remainingPids = pd.read_stata(inputFile).filter(['pid'])
    elif inputFile[-3:] == 'lsx':
        remainingPids = pd.read_excel(inputFile).filter(['pid'])
        
    t0 = time.time()
    islandID = 0
    
    total = remainingPids.count()[0]
    finalcsv = pd.DataFrame()
    finished = False
    
    print('Starting scrape')
    while(not(finished)):
        pid = remainingPids.iloc[0, remainingPids.columns.get_loc('pid')]
        #pid is inserted 3 times because scrapeperson often breaks if only fed one pid
        temp = pd.DataFrame(data={'pid': [pid, pid, pid]})
        size = temp.drop_duplicates().count()[0]
        completeIsland = temp.drop_duplicates();
        growing = True
        try:
            while(growing):
                temp.to_csv(r'in.csv')
                finaldf = pd.DataFrame()
                
                with suppress_stdout():
                    try:
                        self.ScrapePerson()
                    except:
                        print("Invalid pid " + pid)
                outFile = pd.read_csv('out.csv',usecols = ['FSID', 'spouse_FSID', 'kid_FSIDs', 'dad_FSIDs', 'mom_FSIDs'])
                
                #only used on the first pass, gets rid of extra pids needed to run scrapeperson
                if size == 1:
                    outFile = outFile.drop_duplicates()
                    
                outFile = outFile.rename(columns={'FSID': 'pid', 'spouse_FSID' : 'spouse', 'kid_FSIDs' : 'kids',
                                                  'dad_FSIDs' : 'dad','mom_FSIDs' : 'mom'})
                #do by column, rename pid, merge and drop duplicates
                counts = outFile.count()
                
                if counts.get('spouse') > 0:
                    pidSpouse = \
                    (outFile.set_index(outFile.columns.drop('spouse',1).tolist())
                       .spouse.str.split(';', expand=True)
                       .stack()
                       .reset_index()
                       .rename(columns={0:'spouse'})
                       .loc[:, outFile.columns]
                    )
                    pidSpouse = pidSpouse.filter(['spouse']).rename(columns={'spouse':'pid'}).drop_duplicates()
                    finaldf = finaldf.append(pidSpouse,ignore_index=True)
                    
                if counts.get('kids') > 0:
                    pidKids = \
                    (outFile.set_index(outFile.columns.drop('kids',1).tolist())
                       .kids.str.split(';', expand=True)
                       .stack()
                       .reset_index()
                       .rename(columns={0:'kids'})
                       .loc[:, outFile.columns]
                    )
                    pidKids = pidKids.filter(['kids']).rename(columns={'kids':'pid'}).drop_duplicates()
                    finaldf = finaldf.append(pidKids,ignore_index=True)
                    
                if counts.get('dad') > 0:
                    pidDad = \
                    (outFile.set_index(outFile.columns.drop('dad',1).tolist())
                       .dad.str.split(';', expand=True)
                       .stack()
                       .reset_index()
                       .rename(columns={0:'dad'})
                       .loc[:, outFile.columns]
                    )
                    pidDad = pidDad.filter(['dad']).rename(columns={'dad':'pid'}).drop_duplicates()
                    finaldf = finaldf.append(pidDad,ignore_index=True)
                    
                if counts.get('mom') > 0:
                    pidMom = \
                    (outFile.set_index(outFile.columns.drop('mom',1).tolist())
                       .mom.str.split(';', expand=True)
                       .stack()
                       .reset_index()
                       .rename(columns={0:'mom'})
                       .loc[:, outFile.columns]
                    )
                    pidMom = pidMom.filter(['mom']).rename(columns={'mom':'pid'}).drop_duplicates()
                    finaldf = finaldf.append(pidMom,ignore_index=True)
                
                #drops any duplicate pids found, will happen more on later generations
                finaldf = finaldf.drop_duplicates()
                
                #insures that scrapeperson always has more than one pid to run on
                try:
                    if finaldf.count()[0] > 0 and finaldf.count()[0] < 3:
                        finaldf = finaldf.append(finaldf,ignore_index=True)
                        #print(finaldf)
                except:
                    print("Single household")
                
                #appends pids found to the list
                completeIsland = completeIsland.append(finaldf, ignore_index=True).drop_duplicates()
                totalSize = completeIsland.count()[0]
                if size == totalSize or totalSize > 1500:
                    growing = False
                    completeIsland['islandID'] = islandID
                    completeIsland['Count'] = totalSize
                    print("Number of people found: " + str(totalSize))
                else:
                    size = totalSize
                    temp = finaldf
                    if size > 9:
                        print("Found " + str(size) +" in the island so far")
        #something broke so it saves the pids remaining and exports what it has gathered so far
        except:
            try:
                print(sys.exc_info()[0])
                sys.exc_info()[2].traceback.print_exception(limit=5)
            except:
                pass
            remainingPids.to_csv(backUpFile, index=False)
            break
        
        finalcsv = finalcsv.append(completeIsland, ignore_index=True)
        remainingPids = remainingPids[~remainingPids['pid'].isin(completeIsland['pid'])]
        leftover = remainingPids.count()[0]
        print(str(leftover) + ' people left of ' + str(total))
        
        islandID += 1
        if islandID % 25 == 0:
            print()
            t2 = time.time()
            avg_time = (t2 - t0)/islandID 
            print('Avg Time: ' + str(round(avg_time, 3)) + ' Seconds/Island')
            print('Est. time remaining: ' + str(round(avg_time * leftover / 3 / 60, 3)) + ' minutes')
        
        print()
        if leftover == 0:
            finished = True
    
    print("Finished!")
    return finalcsv

if __name__ == '__main__':
    #Change working director to file location  
    os.chdir(r'V:\FHSS-JoePriceResearch\RA_work_folders\Nathan_Winward\AAStats\Islands')
    #Used if not called from familysearch class
    #Put your file here
    yourInputFile = 'chatham_pids.csv'
    #Put a temporary file name here, this will be used to save the pids that have not been scraped if the program crashes
    #This will not save your data if the console is closed, only if it hits errors
    backUpFile = 'leftover_pids.csv' 
    #Used to name the outputfile, will overwrite exsiting file with the same name, should output even if the program crashes
    yourOutputFile = 'chatham_islands.csv'
    #Set to current next id value if you are planning to append to current island list
    fs = FamilySearch('nrwinward','Bluejay77',os.getcwd(),'in.csv','out.csv',auth=True)
    finalcsv = ScrapeIslands(fs, yourInputFile, backUpFile)
    finalcsv.to_csv(yourOutputFile,index=False)