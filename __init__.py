# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 17:26:03 2017

@author: tannerse
"""

import sys
sys.path.append(r'R:\JoePriceResearch\Python\Anaconda3\Lib\site-packages')

import os
import re
from time import time

import requests
from selenium import webdriver

from . import Authenticate
from . import ScrapePerson
from . import ReplaceDeleted
from . import GetRecordHints
# from . import CheckRecords
from . import AttachedCensus
from . import PidFromArk
from . import GetPidFromArk
from . import RAGui
from . import ScrapeRecord
from countyprepper import CountyPrepper
from . import _get_ark
from . import _get_siblings
from . import _get_two
from . import helper_functions
from . import Find
from . import Find_new
from . import google_helpers
from . import DescendancySheet

sys.path.insert(0, 'R:\JoePriceResearch\RA_work_folders\Ben_Branchflower')
import sib_arks_ScrapePerson


class FamilySearch:
    '''
    This is a class to perform the various functions to interact directly with
        Family Search.
    
    The constructor requires a Family Search username, password, and an operating
        directory. An input file, output file, fsid, and arkid are optional.
        
    
    Private Functions:
        __init__          - Initialize the Family Search object.
        _login            - Logs in to Family Search with a username and password, returns a webdriver.
        _finished         - Writes a finished file when the code is done.
        _write_csv        - Writes information to a csv.
        _timer            - Times an iteration of the code and prints the average time and estimated time remaining.
        _remove_non_ascii - Removes all non-ascii characters from a string.
        

    Public Functions:
        Authenticate      - Returns an authentication token for the API.
        Find              - Searches for individuals and returns matches from the Family Tree.
        Find_new          - Searches for individuals and returns matches from the Family Tree. Practice and update.
        Find_pull         - Returns a json with the FS API returns
        ScrapePerson      - Scrapes the information for pids from FamilySearch.
        ReplaceDeleted    - Replaces all the deleted pids in a Google Doc with the correct pids.
        AttachedCensus    - Scrape the information from the census records attached to a set of pids.
        GetPid            - Get all FamilySearch pids attached to a set of ark ids.
        RAGui             - Run the RA interface to interact with Google Sheet projects.
    '''
    
    
    def __init__(self, username, password, directory, infile=None, outfile=None, 
                 fsid=None, arkid=None, county=None, auth=True, login=False):
        '''
        Initializes the FamilySearch object.        
        
        Parameters
        ----------
        username  - Family Search username
        password  - Family Search password
        directory - Operating directory
        infile    - The master input file for data
        outfile   - The name for the result file
        fsid      - Family Search Id for the individual
        arkid     - Ark Id for a specific record on Family Search
        county    - ???
        login     - Login to FamilySearch on initialization
        auth      - Get a valid API token on initialization
        '''
        # Initialize each attribute.
        self.username = username
        self.password = password
        self.directory = directory
        self.county = county
        self.infile = infile
        self.outfile = outfile
        self.id = fsid
        self.arkid = arkid
        
        # constants
        self.CLIENT_ID = 'b0OOX6VXJ1RV' # This is the app key given to the lab
        
        # the connection that will be used
        self.session = requests.Session()
		
        # Change the directory.
        os.chdir(self.directory)
        
        # Set the iteration counter to zero to start.
        self.iter = 0
        
        # Set the total time to zero to start.
        self.time_total = 0.0
        
        # Initialize the person dictionary.
        #self.person = self._create_person()
        
        # Login to FamilySearch if specified.
        if login == True:
            self.driver = self._login()
        if auth == True:
            self.token = self.Authenticate()
        elif self.token is None:
            print("The app token doesn't seem to be working.")
            raise KeyError('Pun intended')

    def _login(self):
        '''
        Logs in to the Family Search website and returns a webdriver.
        
        Returns
        -------
        driver = Selenium webdriver object.
        '''
        #Call chromedriver
        chromedriver = 'R:\\JoePriceResearch\\Python\\chromedriver.exe'
        os.environ['webdriver.chrome.driver'] = chromedriver
        options = webdriver.ChromeOptions()
        options.add_argument('log-level=3')
        driver = webdriver.Chrome(chromedriver, chrome_options=options)
        
        #Open Family Search and login
        driver.implicitly_wait(10)
        driver.get('https://familysearch.org/tree/#view=tree&section=pedigree')
        driver.find_element_by_name('userName').send_keys(self.username)
        driver.find_element_by_name('password').send_keys(self.password)
        driver.find_element_by_id('login').click()
        return driver
    
    
    def _finished(self):
        '''
        This function writes the finished file.
        '''
        # Open the finished file.
        j = open('finished.csv','a')
        
        # Get the number of the infile.
        try:
            infile_num = re.search(r'[0-9]+',self.infile).group()
        except:
            infile_num = self.infile
        
        # Write the infile number.
        j.write(infile_num + '\n')
        
        # Close the open file.
        j.close()
        
        
    def _write_csv(self,write):
        '''
        This function writes the results of a function to a csv.
        
        write - The content to be written to a csv.
        '''
        # Make sure an outfile is specified.
        if self.outfile == None:
            print('\nNo Output File Specified')
            return False
            
        # Write to the outfile.
        j = open(self.outfile,'a')
        j.write(write)
        j.close()
        return True
    
        
    def PrepCounty(self):
        '''
        Uses the CountyPrepper object, and calls its main method
        '''
        cp = CountyPrepper(self.username,self.password,self.county,self.infile,self.outfile)
        cp.prep_data()
    
    
    def _timer(self, switch, row_count=0, numobs=1, ndigits=2):
        '''
        This function times the code and reports average time per person and
            time remaining.
            
        Parameters
        ----------
        switch = Either "on" or "off", indicating whether to start or stop the timer.
        row_count = Number of observations left to do.
        '''
        # Start the timer.
        if switch == 'on':
            self.time_on = time()
            return True
        
        # Stop the timer.
        if switch == 'off':
            self.time_off = time()
            
            # Keep track of total time.
            self.time_total = self.time_total + (self.time_off - self.time_on)
            
            # Increment the iteration counter.
            self.iter = self.iter + numobs
            
            # Keep track of the average time per iteration.
            self.time_av = self.time_total/float(self.iter)
            
            # Print out the results.
            print('Average Time:' + '\t        ' + str(round(self.time_av, ndigits)) + ' Seconds')
            print('Hours Remaining:' + '\t' + str(round((self.time_av * (row_count - self.iter))/3600,2)) + ''.expandtabs(5) + ' Hours\n')
            return True


    def _remove_non_ascii(self, text):
        '''
        This function removes non ascii characters from a string.
        '''
        try:
            stuff = ''.join(i for i in text if ord(i)<128)
        except:
            stuff = ''
        return stuff
    
    # this is something that will be temporarily added to test and should
    # be deleted if found here after 4 June 2018
    test_ScrapePerson = sib_arks_ScrapePerson.test_ScrapePerson
    
    # this is a helper function for DescendancySheet
    #_grab_fsids = DescendancySheet._grab_fsids
    GetDups = DescendancySheet.GetDups
    MakeSheet = DescendancySheet.MakeSheet
    
    # Define separate files as methods.
    Authenticate = Authenticate.Authenticate
    ScrapeFamily = ScrapePerson.ScrapeFamily
    ScrapePerson = ScrapePerson.ScrapePerson
    Find = Find.Find
    FindPerson = Find_new.FindPerson
    _ping_api = Find_new._ping_api
    ReplaceDeleted = ReplaceDeleted.ReplaceDeleted
    AttachedCensus = AttachedCensus.AttachedCensus
    GetRecordHints = GetRecordHints.GetRecordHints
    DescendancySheet = DescendancySheet.DescendancySheet
    # CheckRecords = CheckRecords.CheckRecords
    GetPid = PidFromArk.GetPid
    GetPidFromArk = GetPidFromArk.GetPidFromArk
    RAGui = RAGui.RAGui
    ScrapeRecord = ScrapeRecord.ScrapeRecord
    
    # These functions support ScrapePerson.
    Ping_API = _get_ark.Ping_API
    _get_ark = _get_ark._get_ark
    _get_siblings = _get_siblings._get_siblings
    _get_two = _get_two._get_two

    
    # These are all from the same file -- helper_functions.py
    _parse_name = helper_functions._parse_name
    _parse_date = helper_functions._parse_date
    _parse_place = helper_functions._parse_place
    _scorename = helper_functions._scorename
    _scoreevent = helper_functions._scoreevent
    
    # These are all for interacting with a Google Doc.
    _get_credentials = google_helpers._get_credentials
    _google_read = google_helpers._google_read
    _google_write = google_helpers._google_write
