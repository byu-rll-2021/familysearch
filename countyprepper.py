# -*- coding: utf-8 -*-
"""
Created on Wed May 03 12:23:49 2017

@author: simpsosj

Arguments:
    1. username - your FamilySearch username
    2. password - your FamilySearch password
    3. county - the name of the county of interest (for folder access)
    4. infile - the file to be read in
    5. outfile - the file to be output
"""

# Import dependencies
import os
import sys
import csv
import re
import time
from time import sleep

# Import Logger (for debugging)
# import logging

# to be able to access other paths
sys.path.append('R:\\JoePriceResearch\\Python\\all_code')
sys.path.append('R:/JoePriceResearch/Python/Anaconda3/Lib/site-packages')
sys.path.append('R:/JoePriceResearch/Python/Python27/Lib/site-packages')

# Import selenium dependencies
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementNotVisibleException

"""
Global CSS Selectors
--------------------
These are global CSS selectors that are used within the DataScraper class. When you import datascraper into
your personal python file, it will also include these global selectors. However, these are just used locally.
"""

### Tree Main Page
_TREE_SUBLINK_ARROW = '#ancestorTab > a.pageSubLink.gotoLink'

### Tree ---> Person Submenu
_ADD_UNCONNECTED_PERSON_BUTTON_TREE = '#add-unconnected-person > button'

### Add Unconnected Person Dialog (AUP) <----- these selectors are only valid for EUROPEAN (Western) names
# ------> Anything with "#tree-style" likely needs to be replaced after website rework
_AUP_DIALOG_SUBHEADER = '#fstAddPersonDialogHeaderAndSubheader'
_AUP_POST_SEARCH_DIALOG = '#tree-style > div.fs-global-dialogs.ng-scope > form > div > div'

_AUP_FIRST_NAME_INPUT = '#roman_first'
_AUP_LAST_NAME_INPUT = '#roman_last'

_AUP_MALE_RADIO_BUTTON = '#find-by-name > div > fieldset:nth-child(2) > div > label:nth-child(2)'
_AUP_FEMALE_RADIO_BUTTON = '#find-by-name > div > fieldset:nth-child(2) > div > label:nth-child(4)'
_AUP_DECEASED_RADIO_BUTTON = '#find-by-name > div > fieldset:nth-child(3) > label:nth-child(5)'

_AUP_NEXT_BUTTON = '#_content > div.modal-content.style-scope.fs-add-person > div.dialog-buttons.style-scope.fs-add-person > div.form-buttons.style-scope.fs-add-person > button.fs-button.fs-button--recommended.next-button.style-scope.fs-add-person'
_AUP_CREATE_NEW_BUTTON = '#_content > div.modal-content.style-scope.fs-add-person > div.dialog-buttons.style-scope.fs-add-person > div.search-result-buttons.style-scope.fs-add-person > div > button.fs-button.fs-button--recommended.create-person-button.style-scope.fs-add-person'

_AUP_NO_MATCH_FOUND_ALERT = '#_content > div.modal-content.style-scope.fs-add-person > div.dialog-content.style-scope.fs-add-person > div > div.search-results-template.style-scope.fs-add-person > div.search-results-heading.no-match.style-scope.fs-add-person'
_AUP_NO_MATCH_ADD_NEW_BUTTON = '#_content > div.modal-content.style-scope.fs-add-person > div.dialog-buttons.style-scope.fs-add-person > div.search-result-buttons.style-scope.fs-add-person > div > button.fs-button.fs-button--recommended.create-person-button.style-scope.fs-add-person'

_AUP_NEW_PERSON_BOX = '#tree-style > div.fs-global-dialogs.ng-scope > form > div > div > div > div > div.fs-dlg__header > div.fs-dlg__sub-title > div > div'

### Person Page
_PERSON_PAGE_BIRTH_DATE = '#LifeSketchVital > div > div.details > div:nth-child(3) > div.conclusionRow.conclusionData > div.dataCell > a > span.datePart'
_PERSON_PAGE_BIRTH_PLACE = '#LifeSketchVital > div > div.details > div:nth-child(3) > div.conclusionRow.conclusionData > div.dataCell > a > span.placePart'
_PERSON_PAGE_EDIT_BIRTH = '#LifeSketchVital > div > div.details > div.conclusion.extended > div.conclusionMenu > a.editConclusion'
_PERSON_PAGE_DELETE_PERSON = '#Tasks > div > a.person-link.fs-icon-trash'

# --> deleting person
_DELETE_PAGE_TEXT_BOX = '#deleteAncestorModal > div.deleting-details > div:nth-child(9) > textarea'
_DELETE_PAGE_REVIEWED_BUTTON = '#deleteAncestorModal > div.deleting-details > div:nth-child(9) > p:nth-child(5) > label > input'
_DELETE_PAGE_INCLUDED_STATEMENT_BUTTON = '#deleteAncestorModal > div.deleting-details > div:nth-child(9) > p:nth-child(6) > label > input'
_DELETE_PAGE_DELETE_BUTTON = '#deleteAncestorModal > div.deleting-details > div:nth-child(9) > p.actions > input'

# --> adding spouse and children
_ADD_OR_FIND_SPOUSE_BUTTON_PERSON_PAGE = '#FamilyMembers > div > div.family-members-wrapper.fs-person--light > section.spouses-and-children.ng-scope.ng-isolate-scope > div > div > div.couple-wrapper > div.person-wrapper.unknown-spouse > button'
_ADD_CHILD_BUTTON_PERSON_PAGE = '#FamilyMembers > div > div.family-members-wrapper.fs-person--light > section.spouses-and-children.ng-scope.ng-isolate-scope > div > div > div.children-wrapper > div > ol > li > button'
_HAS_CHILDREN_ADD_CHILD_BUTTON_PERSON_PAGE = '#FamilyMembers > div > div.family-members-wrapper.fs-person--light > section.spouses-and-children.ng-scope.ng-isolate-scope > div > div > div.children-wrapper > div > ol > li.person-wrapper.add-placeholder > button'
_ADD_PARENT_BUTTON_PERSON_PAGE = '#FamilyMembers > div > div.family-members-wrapper.fs-person--light > section.parents-and-siblings.ng-scope.ng-isolate-scope > button.add-parent.fs-icon-before-add'
_ADD_PARENT_SPOUSE_BUTTON_PERSON_PAGE = '#FamilyMembers > div > div.family-members-wrapper.fs-person--light > section.parents-and-siblings.ng-scope.ng-isolate-scope > div > div > div.couple-wrapper > div.person-wrapper.unknown-spouse > button'
_FIND_BY_ID_NUMBER_BUTTON = '#tree-style > div.fs-global-dialogs.ng-scope > form > div > div > div > div > div.fs-dlg__buttons > div > div > div > button.fs-button.fs-button--minor.fst-add-person__by-id.fs-icon-before-search.ng-scope'
_ID_NUMBER_INPUT = '#tree-style > div.fs-global-dialogs.ng-scope > form > div > div > div > div > div.fs-dlg__body > div > div.fst-add-person__body.fst-add-person__add_by_id.ng-scope > div > span.fst-add__id-shell > input'
_FIND_BUTTON = '#tree-style > div.fs-global-dialogs.ng-scope > form > div > div > div > div > div.fs-dlg__buttons > div > div > div > button.fs-button.fs-button--recommended'
_ADD_PERSON_BUTTON = '#tree-style > div.fs-global-dialogs.ng-scope > form > div > div > div > div > div.fs-dlg__body > div > div.fst-add-person__body.fst-add-person__results.ng-scope > div > div > div > div > div.person-add-stuff.ng-scope > button'


### Post Tree Update Buttons
_RECENTS_BUTTON = '#recentsBtn'
_ADD_UNCONNECTED_PERSON_BUTTON = '#tree-style > div.fs-global-dialogs.ng-scope > div:nth-child(8) > div > div > div > div > div.fs-dlg__body > div > div:nth-child(3) > div.fst-history-list__create_person > button > a'

"""
CountyPrepper
-------------
This class is used to prep the ready_dates.csv (or whatever file you enter) file by
adding any missing individuals to FamilySearch, scraping the date the were added to
the tree, and adding additional lines to the .csv file to assist RAs in manually
scraping data from FamilySearch.

@params:
    username - your (or any valid) FamilySearch username
    password - your (or any valid) FamilySearch password
    county - the county that the current individuals are from
    infile - the file to be read in (this file should have a standard format, as
    the order of the columns matter for use in this file)
    outfile - the name of the where new info should be written (different name than infile)
    
@methods:
    
"""
class CountyPrepper:
    # this is the function that initializes our object
    # to use this object, pass in a selenium webdriver object
    def __init__(self, username, password, county, infile, outfile):
        # store username and password
        self.username = username
        self.password = password

        # save files to print to
        self.infile = infile
        self.outfile = outfile
        self.county = county

        # call login function, save driver
        self._login()
        # logging.basicConfig(filename='debug.log',level=logging.DEBUG)

        # start datacount (use this to eventually keep track of time)
        self.data_count = 0

        # start person created count
        self.last_hhid = ''
        self.person_created_flag = False
        
        # flag for if we should refresh the page and try again
        self.refresh_flag = False
        self.try_again_flag = False

        # for keeping track of what line we are on
        self.line = 0
        self.head_of_household = self._create_person()
        
        # we need to keep this, because I ran into a polygamist once...
        self.previous_person_relationshp = ''


    """
    prep_data()
    -----------
    Function to be called after creating a 'CountyPrepper' object. Reads in
    the file used when initializing 'CountyPrepper', and lien by line adds
    individuals to the tree and/or scrapes the date they were added.

    Writes all individuals to a file using the specified outfile.

    Additional Functions:
        _scrape_date_added()
        _add_person()

    @params: none
    @return: none
    """
    def prep_data(self):
        # do everything in the "master prep" file
        # also do the things from the other files
        latest_ra_id = self._get_starting_point()

        # read in file, save in 'data'
        data = self._read_file()
        print(len(data))

        # print header line
        if(latest_ra_id == ''):
            self._write_first_line()

        # start flag
        start_flag = False

        # this used to be surrounded by a "try, except" clause, but I got rid of it
        for line in data:
            self.line = self.line + 1
            
            # creates empty person object
            self.person = self._create_person()
                                    
            # populates with data from .csv file
            self._store_current_person(line)            
            
            # skips any header lines
            if (start_flag):
                    
                # only ook at person if they are an immediate family member
                if (self._is_immediate_family_member()):
        
                    # determine whether individual is "Head of Household"
                    head = (self.person['relation_to_head'] == 'Head')
                    
                    # make sure and check this before we set head_of_household to be this person
                    if (head and (self.person['hhid'] == self.head_of_household['hhid'])):
                        print('Error: There are 2 heads of household')
                    elif (self.previous_person_relationshp == 'Wife' and
                          self.person['relation_to_head'] == 'Wife'):
                        print('Error: More than one wife')
                    else:
                        # store 'Head of Household'
                        if (head):
                            self.head_of_household = self.person
                            # we will use this person to attach their family to their record
        
                        # add person
                        self._add_person(head)
                        
                        # write them to outfile
                        self._write_person_to_outfile()
            else:
                if (self.person['id'] == latest_ra_id or
                     latest_ra_id == ''):
                     start_flag = True
                    
                    
            self.previous_person_relationshp = self.person['relation_to_head']

        # write finished do file when done
        endfile = open('finished.csv', 'a')
        endfile.write(' ' + self.infile + '\n')
        endfile.close()
     



    """
    _add_person()
    -------------
    If given person is not attached to the record, they are created in family search
    and attached to the record. If, for some reason, somebody IS attached to the record,
    we scrape this person's FSID and scrape the date they were added to the tree.

    Additional Functions:
        _check_record_attached()
        _add_unconnected_person()
        _scrape_date_added()

    @param: none
    @return: none (considering returning a "success" boolean)
    """
    def _add_person(self, head):
        # format and access webpage
        ARK_ID_PAGE = 'https://familysearch.org/ark:/61903/1:1:{}'
        self.driver.get(ARK_ID_PAGE.format(self.person['arkid']))

        # See if someone is attached
        attached = self._check_record_attached()

        # as long as there aren't already attachments, this piece runs
        if (attached == False):
            
            if (float(self.person['match_score']) > 7):
                # assign fsid to the match_id, and use it to attach the record
                self.person['fsid'] = self.person['match_id']
                self.person['method'] = 'match'
                self.person['year_added'] = self._scrape_date_added(self.person['fsid'])
                
            else:
                self._add_unconnected_person()

            if (not head):
                self._attach_to_head()            
                
            ## attach whichever person to the record
            # go to record page
            try:
                ARK_ID_PAGE = 'https://familysearch.org/ark:/61903/1:1:{}'
                self.driver.get(ARK_ID_PAGE.format(self.person['arkid']))
            except:
                print("ERROR: Record '" + self.person['arkid'] + "' doesn't exist.")
                return

            # gets shadow root and associated elements
            element_tree = ['#main-content-section > div > record-details-renderer','section.right > record-details-tools']
            self._click_in_shadow_root(element_tree,'div > a', False)
            
            # look for the space where you can search for IDs
            self._driver_wait('visible', By.ID, 'id-input', True)

            # enters in the fsid of the person in the 'find a match in FamilyTree' id entry box
            self._send_keys(By.ID, 'id-input', self.person['fsid'])
                
            self.driver.find_element_by_id('id-input').send_keys(Keys.ENTER)

            # waits until the 'add' button shows up to continue
            sleep(.5)

            # presses 'add' for up to five events (birth,death,etc.)
            for i in range(5):
                selector = '#confirm_event_{} > button.fs-button.fs-button--minor.confirm-action.confirm-add > span'
                self._click_element(By.CSS_SELECTOR, selector.format(i), 10, False)
                

            # waits for the 'attach' button to show up
            # clicks 'attach'
            self._driver_wait('visible', By.CSS_SELECTOR, '#PersonOfRecordTableDiv > table > tbody > tr.attach-confirm-row.ng-scope > td > div.buttons.tags-source > button.fs-button.fs-button--recommended', False)
            self._click_element(By.CSS_SELECTOR,'#PersonOfRecordTableDiv > table > tbody > tr.attach-confirm-row.ng-scope > td > div.buttons.tags-source > button.fs-button.fs-button--recommended', 10, False)


        ###THIS PART NEEDS HELP
        else: # that is, if there's already a person attached to the record
            # set method to 'linked'           
            self.person['method'] = 'linked'        
            
            text = self.driver.find_element_by_css_selector('html').text
            if re.search('Multiple People', text):
                element_tree = ['#main-content-section > div > record-details-renderer','section.right > record-details-tools']
                self._click_in_shadow_root(element_tree, 'div > button', True)
                
                sleep(1)
                text = self.driver.find_element_by_css_selector('html').text
                self.person['fsid'] = re.findall('[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9]',re.search('Attached to:[\s\S]+',text).group())[0]
            else:
                while not re.search('[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9]',re.search('Attached to:[\s\S]+',text).group()):
                    text = self.driver.find_element_by_css_selector('html').text
                    sleep(1)
                self.person['fsid'] = re.findall('[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9]',re.search('Attached to:[\s\S]+',text).group())[0] 
        
            self.person['year_added'] = self._scrape_date_added(self.person['fsid'])



    """
    _is_immediate_family_member()
    -----------------------------
    Checks current person to see if they are an immediate relative to head of household

    @params: none
    @return: boolean describing whether individual is immediate family member to
            'Head of Household'
    """
    def _is_immediate_family_member(self):
        if (self.person['relation_to_head'] == 'Head' or self.person['relation_to_head'] == 'Wife' or
            self.person['relation_to_head'] == 'Son' or self.person['relation_to_head'] == 'Daughter' or
            self.person['relation_to_head'] == 'Mother' or self.person['relation_to_head'] == 'Father'):
                return True



    """
    _add_unconnected_person()
    -------------------------
    Adds an unconnected person to FamilySearch using the information given from
    the read .csv file.

    Additional Functions:
        _standardize_birth_post_add()

    @params: none
    @return: none
    """
    def _add_unconnected_person(self):
        # Click the search button and fill the search fields.
        try:
            # flag that we created someone
            self.person_created_flag = True
            
            # the general pedigree tree page
            self.driver.get('https://familysearch.org/tree')
            self._driver_wait('clickable', By.CSS_SELECTOR, _RECENTS_BUTTON, True)
            sleep(1)
            
            # we wait twice, because the webpage takes a second to load
            self._driver_wait('clickable', By.CSS_SELECTOR, _RECENTS_BUTTON, True)

            # the link with the dropdown menu to 'add unconnected person'
            self._click_element(By.CSS_SELECTOR, _RECENTS_BUTTON, 10, False)
            sleep(.5)

            # clicks on 'add unconnected person' button
            self._click_element(By.CSS_SELECTOR, _ADD_UNCONNECTED_PERSON_BUTTON_TREE, 10, False)
            sleep(.5)

            # waits for first name input to be visible
            self._driver_wait('visible', By.CSS_SELECTOR, _AUP_FIRST_NAME_INPUT, False)
            sleep(.5)

            # inputs first name
            self._send_keys(By.CSS_SELECTOR, _AUP_FIRST_NAME_INPUT, self.person['name']['first'])

            # click 'male' or 'female'
            if self.person['gender'] == 'Male':
                self._click_element(By.CSS_SELECTOR, _AUP_MALE_RADIO_BUTTON, 10, False)
            else:
                self._click_element(By.CSS_SELECTOR, _AUP_FEMALE_RADIO_BUTTON, 10, False)

            # click 'deceased' radio button
            self._click_element(By.CSS_SELECTOR, _AUP_DECEASED_RADIO_BUTTON, 10, False)

            # Enter birthdate and place in search fields
            birth = self.driver.find_elements_by_css_selector('#input')

            if (self.person['birth']['month'] != ''):
                birth[0].send_keys(self.person['birth']['month'] + ' ' + self.person['birth']['year'])
            else:
                birth[0].send_keys(self.person['birth']['year'])
            birth[1].send_keys(self.person['birth']['place'])

            # Enter last name
            self._send_keys(By.CSS_SELECTOR, _AUP_LAST_NAME_INPUT, self.person['name']['last'])

            # Click 'NEXT'
            self._click_element(By.CSS_SELECTOR, _AUP_NEXT_BUTTON, 10, False)

        except KeyboardInterrupt:
            sys.exit(1)
        except:
            print("failed to create person")

        # Add the person to the tree.
        try:
            sleep(1)

            # check if no match is found
            WebDriverWait(self.driver,2).until(EC.visibility_of_element_located((By.CSS_SELECTOR, _AUP_NO_MATCH_FOUND_ALERT)))
            print('No Match Found')
            
            # if no matches are found, click "add person" button
            self._driver_wait('clickable', By.CSS_SELECTOR, _AUP_NO_MATCH_ADD_NEW_BUTTON, False)
            self._click_element(By.CSS_SELECTOR, _AUP_NO_MATCH_ADD_NEW_BUTTON, 10, False)

        except KeyboardInterrupt:
            sys.exit(1)
        except:
            # will continue here if the alert doesn't show up (meaning we found matches)
            self._driver_wait('clickable', By.CSS_SELECTOR, _AUP_CREATE_NEW_BUTTON, False)
            self._click_element(By.CSS_SELECTOR, _AUP_CREATE_NEW_BUTTON, 10, False)


        # this is in case something shows up that the 'service is down', but we are creating someone new anyway,
        # so the 'create possible duplicate' isn't really a big deal

        # Make sure the page is loaded.
        self._driver_wait('visible', By.CSS_SELECTOR, '#LifeSketchVital > div > div.details > div:nth-child(3) > div.conclusionRow.conclusionData', True)

        # ---------- Scrape the new id -----------
        sleep(1)
        
        # find the fsid
        self.person['fsid'] = str(re.search('[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9]',str(self.driver.current_url)).group())
        
        # set year added to '2017' because we just barely made this person
        self.person['method'] = 'created'
        self.person['year_added'] = '2017'

        # standardize birthdate and birthplace
        if(self.person['birth']['year'] != '' or self.person['birth']['month'] != '' or self.person['birth']['place'] != ''):
            self._standardize_birth_post_add()
            
        # immediately adds the most recently added person to a .csv file
        self._write_person_added_to_tree(self.person['fsid'])




    """
    _attach_to_head()
    ---------------------
    Attaches the current person to the "Head of Household" if they are an immediate
    family member. Extended family members are skipped.
    
    @params: none
    @return: none
    """ 
    def _attach_to_head(self):
        
        # Go to person page
        try:
            HEAD_OF_HOUSEHOLD_PAGE = 'https://www.familysearch.org/tree/person/details/{}'
            self.driver.get(HEAD_OF_HOUSEHOLD_PAGE.format(self.head_of_household['fsid']))
        except:
            print("ERROR: Record '" + self.head_of_household['fsid'] + "' doesn't exist.")
            return
                
        
        if (self.person['relation_to_head'] == 'Wife'):
            # Wait for and click "Add Spouse" button
            self._driver_wait('clickable', By.CSS_SELECTOR, _ADD_OR_FIND_SPOUSE_BUTTON_PERSON_PAGE, True)
            self._click_element(By.CSS_SELECTOR, _ADD_OR_FIND_SPOUSE_BUTTON_PERSON_PAGE, 10, False)
            
        elif (self.person['relation_to_head'] == 'Son' or self.person['relation_to_head'] == 'Daughter'):
            # Wait for and click "Add Child" button
            self._driver_wait('clickable', By.CSS_SELECTOR, _ADD_PARENT_BUTTON_PERSON_PAGE, True)

            try:
                # try to click this button
                self.driver.find_element_by_css_selector(_ADD_CHILD_BUTTON_PERSON_PAGE).click()
            except:
                # if they have children, click this one
                self._click_element(By.CSS_SELECTOR, _HAS_CHILDREN_ADD_CHILD_BUTTON_PERSON_PAGE, 10, False)
            
        elif (self.person['relation_to_head'] == 'Mother' or self.person['relation_to_head'] == 'Father'):
            # Wait for and click "Add Child" button
            self._driver_wait('clickable', By.CSS_SELECTOR, _ADD_PARENT_BUTTON_PERSON_PAGE, True)
        
            try:
                # try to add a parent's spouse
                self.driver.find_element_by_css_selector(_ADD_PARENT_SPOUSE_BUTTON_PERSON_PAGE).click()
            except:
                # add a new parent
                self._click_element(By.CSS_SELECTOR, _ADD_PARENT_BUTTON_PERSON_PAGE, 10, False)
                
        else:
            return
        
        # Wait for and click "Find by ID Number" button
        self._driver_wait('clickable', By.CSS_SELECTOR, _FIND_BY_ID_NUMBER_BUTTON, False)
        sleep(.5)
        self._click_element(By.CSS_SELECTOR, _FIND_BY_ID_NUMBER_BUTTON, 10, False)
        
        # Wait for input box, and type in FSID
        self._driver_wait('visible', By.CSS_SELECTOR, _ID_NUMBER_INPUT, False)
        sleep(.5)
        self._send_keys(By.CSS_SELECTOR, _ID_NUMBER_INPUT, self.person['fsid'])
        sleep(.5)
        
        # Click "Find" button
        self._click_element(By.CSS_SELECTOR, _FIND_BUTTON, 10, False)
        
        # Click "Add Person" button
        self._driver_wait('clickable', By.CSS_SELECTOR, _ADD_PERSON_BUTTON, False)
        sleep(.5)
        self._click_element(By.CSS_SELECTOR, _ADD_PERSON_BUTTON, 10, False)
        
        # Back to "Add Person"




    """
    _attach_full_record()
    ---------------------
    DON'T USE THIS FUNCTION FOR NOW!
    
    Until I figure out another way to use this.

    Current testing id: KK79-Y5H (otto klatt)
    """ 
    def _attach_full_record(self):
        self._driver_wait('clickable', By.CSS_SELECTOR, '#dst_root > div > div.gender-icon.male > div.name > button', True)
        sleep(1)

        total_elements_add = self.driver.find_elements_by_xpath("//button//span[contains(text(), 'Add')]")
        iterations = len(total_elements_add)

        # this determines if we search for FSIDs
        # attached_records = False

        while(iterations > 0):
            # attached_records = True
            elements_add = self.driver.find_elements_by_xpath("//button//span[contains(text(), 'Add')]")

            # clicks the 'add' button from main record page
            self._click_element_no_selector(elements_add[0], 10)

            # check for visibility of this element
            sleep(1)
            self._driver_wait('visible', By.CLASS_NAME, 'gender-record-medium', False)
            sleep(1)

            # standardize and create new person
            # if it doesn't work, we break, set possible matches to true, and try again
            try:
                # standardize birthdate
                sleep(.5)
                if(self._remove_non_ascii(self._get_element_text(By.CSS_SELECTOR, '#si-date1')) != ''):
                    self._standardize(By.CSS_SELECTOR, '#si-date1')

                # standardize birthplace
                sleep(.5)
                if(self._remove_non_ascii(self._get_element_text(By.CSS_SELECTOR, '#si-date2')) != ''):
                    self._standardize(By.CSS_SELECTOR, '#si-place2')
                
                # click the 'deceased' radio
                sleep(.5)
                self._click_element(By.CSS_SELECTOR, '#add-dead', 50, False)

                self.driver.find_element_by_css_selector('#add-panel > div.panel-footer > span.position-relative > button').click()                      
                possible_matches_exist = False
                sleep(5)
            except:
                print('possible matches exist')
                possible_matches_exist = True

            # click this button to advance (if possible matches exist)
            if (possible_matches_exist):
                self._click_element(By.CSS_SELECTOR, '#add-panel > div.panel-footer > span:nth-child(1) > button', 10, False)

                # wait for clickability of 'create new person' (in actual create person panel)
                sleep(.5)
                self._driver_wait('clickable', By.CSS_SELECTOR, '#add-panel > div.panel-footer > span.position-relative > button', False)

                # standardize birthdate
                sleep(.5)
                if(self._remove_non_ascii(self._get_element_text(By.CSS_SELECTOR, '#si-date1')) != ''):
                    self._standardize(By.CSS_SELECTOR, '#si-date1')

                # standardize birthplace
                sleep(.5)
                if(self._remove_non_ascii(self._get_element_text(By.CSS_SELECTOR, '#si-date2')) != ''):
                    self._standardize(By.CSS_SELECTOR, '#si-place2')
                
                # click the 'deceased' radio
                sleep(.5)
                self._click_element(By.CSS_SELECTOR, '#add-dead', 50, False)

                # click 'create new person'
                sleep(.5)
                self._click_element(By.CSS_SELECTOR, '#add-panel > div.panel-footer > span.position-relative > button', 50, False)

                # wait for attach screen to load
                sleep(5)

            # clicks to add each attribute to the person's profile from the record
            for i in range(5):
                selector = '#confirm_event_{} > button.fs-button.fs-button--minor.confirm-action.confirm-add > span'
                self._click_element(By.CSS_SELECTOR, selector.format(i), 2, False)

            # wait for a second
            sleep(5)
            sleep(1)

            # finds the final attach button, and attaches it
            attach_buttons = self.driver.find_elements_by_xpath("//button[@type='button'][contains(text(), 'Attach')]")
            
            for button in attach_buttons:
                if (button.text == 'Attach'):
                    self._click_element_no_selector(button, 50)

            sleep(1)
            iterations = iterations - 1
            
        
        """
        # only run this is we attached any records
        if (attached_records):
            # this doesn't work... think of a new way to fix this....
            # but honestly, i don't think is a big deal because you can usually find
            # the people who were attached using this method by looking at the head of household
            # also, I have fixed the issue of attaching multiple times :) good news!
            
            # get all FSIDs of newly created people
            elements_id = self.driver.find_elements_by_xpath("//span[@class='fs-person-details__id']")
            
            for element in elements_id:
                fsid = self._get_element_text_no_selector(element)
                self._write_person_added_to_tree(fsid)
        """    



    """
    _scrape_date_added()
    --------------------
    Finds the date that a given individual (associated with the given FamilySearch ID)
    was added to FamilySearch. If the given individual has been merged, this function
    also acts recursively, and calls itself with the FSID of the individual.

    @params: fsid - FamilySearch ID of individual to be scraped
    @return: year_added - the year that individual was added to FamilySearch
    """
    def _scrape_date_added(self, fsid):
        # goes to the person's changelog
        site = 'https://familysearch.org/tree/person/{}/changelog'
        self.driver.get(site.format(fsid))

        # wait for this element to be visible
        self._driver_wait('visible', By.XPATH, '//*[@id="personHeaderWatch"]/div/a', True)
        sleep(3)

        # gets the last changelog entry as text  
        try:
            if (self._check_element_exists(By.CLASS_NAME, 'changeLogEntry')):
                # get last entry text
                last_entry = self.driver.find_elements_by_class_name('changeLogEntry')[len(self.driver.find_elements_by_class_name('changeLogEntry')) - 1]
                last_entry_text = self._remove_non_ascii(last_entry.text)
                
                # get record record creator
                created_by = last_entry.find_element_by_css_selector('div.info.cell > span > a')
                self.person['created_by'] = self._remove_non_ascii(created_by.text)
        except IndexError:
            return ''

        # initialize important variables
        found = False
        start_index = 0
        year_added = ''

        # looks through the changelog entry to find the year it was made
        while(found == False):
            found_index = last_entry_text.find('20', start_index)

            if found_index == -1:
                year_added = ''
                found = True
            else:   
                if last_entry_text[found_index + 2] != ' ':  # in case the log entry was on 20 xxxxxxxx, 20xx
                    year_added = last_entry_text[found_index:(found_index + 4)]
                    found = True
                else:
                    start_index = found_index + 2
                    found = False
        
        # returns because 2012 is the earliest it could be added
        if(year_added == '2012'):
            return year_added

        # checks for merges in the changelog
        num_merges = len(self.driver.find_elements_by_class_name('group'))  # only merges show up under the group class
        num = 0

        # if num_merges > 1
        # finds the fsid of the formerly merged person, and runs the function for that person
        while(num_merges > 0 and num < len(self.driver.find_elements_by_class_name('changeLogEntry'))):

            element_id = 'changeLogEntryIndex_{}'

            if re.search('Merge Completed', str(self._remove_non_ascii(self.driver.find_element_by_id(element_id.format(num)).text))):
                num_merges = num_merges - 1
                mergeid = str(self.driver.find_element_by_id(element_id.format(num)).find_elements_by_class_name('char')[1].find_element_by_class_name('name').get_attribute('data-event-data'))
                
                year_added_2 = self._scrape_date_added(mergeid)
                
                if int(year_added_2) < int(year_added):  # if the year of the merged person's creation is earlier, we use that one. 
                    year_added = year_added_2
                self.driver.back()

            num = num + 1

        # return year added
        return year_added



    """
    _standardize_birth_post_add(self):
    ----------------------------------
    Standardizes the birthplace and birthdate of the current person.
    (Given that we've already accessed their page)

    @params: none
    @return: none
    """
    def _standardize_birth_post_add(self):

        # we wait in the previous function
        no_date = False
        # birth date and place
        try:
            birth = self.driver.find_element_by_css_selector(_PERSON_PAGE_BIRTH_DATE)
        except:
            birth = self.driver.find_element_by_css_selector(_PERSON_PAGE_BIRTH_PLACE)
            no_date = True

        
        if birth.text != '':
            self._click_element_no_selector(birth, 10)
            sleep(.75)
            self._click_element(By.CSS_SELECTOR, _PERSON_PAGE_EDIT_BIRTH, 10, False)
            
            # standardize the date and place (Basically finishes making the person)
            if (not no_date):
                self._standardize(By.CSS_SELECTOR, '#vital-conclusion-birth-date')
            self._standardize(By.CSS_SELECTOR, '#vital-conclusion-birth-place')
            
            # click confirm
            self._click_element(By.CSS_SELECTOR, '#LifeSketchVital > div > div.details > div.conclusion.extended.edit > div.buttonRow > button', 10, False)
            sleep(1)
  

    """
    _get_shadow_root()
    ------------------
    Checks (given a record we have accessed) whether the record is attached
    to a specific group of individuals or not.

    @params: none
    @return: boolean attached; True if attached, False otherwise
    """
    def _get_shadow_root(self, elements):
        shadow_root = self.driver.execute_script('return arguments[0].shadowRoot', self.driver.find_element_by_css_selector(elements[0]))
        for x in range(1,len(elements)):
            shadow_root = self.driver.execute_script('return arguments[0].shadowRoot', shadow_root.find_element_by_css_selector(elements[x]))
        return shadow_root


    """
    _click_in_shadow_root()
    -----------------------
    Checks (given a record we have accessed) whether the record is attached
    to a specific group of individuals or not.

    @params: none
    @return: boolean attached; True if attached, False otherwise
    """
    def _click_in_shadow_root(self, elements, selector, refresh):
        stale = True
        attempts = 0        
        while (stale and attempts < 10):
            if (refresh and attempts == 10- 1):
                self.driver.refresh()
                attempts = 0
            else:
                try:
                    shadow_root = self._get_shadow_root(elements)
                    shadow_root.find_element_by_css_selector(selector).click()
                    stale = False
                except NoSuchElementException:
                    print('No such element found. Could not click ' + elements[len(elements)])
                    stale = False
                except StaleElementReferenceException:
                    stale = True
                    attempts = attempts + 1
                except ElementNotVisibleException:
                    attempts = attempts + 1


    """
    _check_record_attached()
    ------------------------
    Checks (given a record we have accessed) whether the record is attached
    to a specific group of individuals or not.

    @params: none
    @return: boolean attached; True if attached, False otherwise
    """
    def _check_record_attached(self):
        sleep(2)
        text = self.driver.find_element_by_css_selector('html').text
    
        if re.search('Attached to:', text):
            return True
        else:
            print('false')
            return False



    """
    _check_all_linked()
    -------------------
    Never used.... may not be necessary...

    """
    def _check_all_linked(self):
        
        try:
            add_buttons = self.driver.find_elements_by_xpath("//*[contains(text(), 'Add')]")
            compare_buttons = self.driver.find_elements_by_xpath("//*[contains(text(), 'Compare')]")
        except:
            pass

        for i in range(len(add_buttons)):
            if (add_buttons[i].text == 'Add'):
                return False

        for i in range(len(compare_buttons)):
            if (add_buttons[i].text == 'Compare'):
                return False

        return True



    """
    _write_first_line()
    -------------------
    Writes the header of of the .csv outfile.

    @params: none
    @return: none
    """
    def _write_first_line(self):
        # prints the variable names as first row
        j = open(self.outfile, 'a')
        j.write('volunteer' + ',' + 'fsid' + ',' + 'method' + ',' + 'match_score' + ',' + 'match_id' + ',' + 'name' + ',' + 'sex_code' + ',' + 
                'birth_place' + ',' + 'birth_date' + ',' + 'relate' + ',' + 'hhid' + ',' + 'person_of_interest' + ',' +
                'county' + ',' + 'id' + ',' + 'created_by' + ',' + 'year_added' + '\n')
        j.close()



    """
    _write_person_to_outfile()
    -----------------------
    Writes currently stored person to the specified outfile (.csv).

    @params: none
    @return: none
    """
    def _write_person_to_outfile(self):
        j = open(self.outfile, 'a')
        j.write('' + ',' + self.person['fsid'] + ',' + self.person['method'] + ',' + self.person['match_score'] + ',' + self.person['match_id'] + ',' +
            self.person['name']['first'] + ' ' + self.person['name']['last'] + ',' + self.person['gender'] + ',' + self.person['birth']['place'] + ',' +
            self.person['birth']['month'] + ' ' + self.person['birth']['year'] + ',' + self.person['relation_to_head'] + ',' + self.person['hhid'] + ',' + 
            self.person['person_of_interest'] + ',' + self.person['county'] + ',' + self.person['id']  + ',' +
            self.person['created_by'] +  ',' + self.person['year_added'] + '\n')
        j.close()



    """
    _read_file()
    ------------
    Reads in a given CSV file and stores each row on in a "data" object. This
    object is then returned to be used in another function.

    Standard CSV formats have been made by Tanner, the scrape functions in this
    object assume that standard format.

    @params: none (file saved in 'self')
    @return: data from file, array of 'rows'
    """
    def _read_file(self):
        with open(self.infile, 'r') as csvfile:
            reader = csv.reader(csvfile)
            data = []
            for line in reader:
                data.append(line)
                # increment number of individuals in the list
                self.data_count = self.data_count + 1
            return data



    """
    _store_current_person(line)
    -----------------------------
    Given a line from a .csv file, this code stores the information
    in a 'person' dictionary in 'self'.

    @params: one line from the '.csv' file
    @return: none
    """
    def _store_current_person(self, line):
        # gather general information
        self.person['hhid'] = line[0]
        self.person['person_of_interest'] = line[1]
        self.person['fsid'] = ''
        self.person['arkid'] = line[4]
        self.person['gender'] = line[6]
        self.person['relation_to_head'] = line[9]
        self.person['id'] = line[10]

        # parse birth information
        birth = line[7]
        index = birth.find(' ')
        if (index > -1):
            birth_month = birth[:index]
            self.person['birth']['month'] = birth_month
        birth_year = birth[(index + 1):]

        # parse name (first and last)
        name = line[5]
        index = name.find(' ')
        first_name = self._remove_non_ascii(name[:index])
        last_name = self._remove_non_ascii(name[(index +  1):])

        if(last_name.find(' ') != -1):
            first_name = first_name + ' ' + (last_name[:last_name.find(' ')]) # append middle initial to first name
            last_name = last_name[last_name.find(' ') + 1:] # reassign last_name to actual last name
        
        if first_name[:4] == last_name[:4]: #handles cases where there is no first name listed. 
            first_name = ''

        # enter birth
        self.person['birth']['year'] = birth_year
        self.person['birth']['place'] = line[8]

        # enter name
        self.person['name']['first'] = first_name
        self.person['name']['last'] = last_name

        # determine match type
        self.person['match_score'] = line[2]
        self.person['match_id'] = line[3]
        self.person['method'] = ''

        # add year added
        try:
            year_added = line[12]
        except:
            year_added = ''

        self.person['year_added'] = year_added



    """
    _define_match_type(match_score, match_id)
    --------------------
    Using the match score, this determines whether this individual was linked,
    matched, or not found. If an error occured, the function returns "error" in
    match_type variable.

    @params:
        match_score - match score from '.csv' infile
        match_id - the fsid individual that could possibly be the match
    @return: retuns string containing match_type (linked, match(#), *blank*[for
            not found], or ERROR)
    """
    def _define_match_type(self, match_score, match_id):
        try:
            match_score = float(match_score) ##have to use float here because it includes .5

            if(len(self.person['fsid']) > 5 and (match_score < 5 or self.person['fsid'] != match_id)):
                method = 'linked'
            else:
                if (match_score > 4.5 and self.person['fsid'] == match_id):
                    method = 'match (' + str(match_score) + ')'
                else:
                    method = ''
        except ValueError:
            method = 'ERROR'
        except:
            method = 'ERROR'

        return method



    """
    _driver_wait(wait_for, search_by, selector)
    --------------
    Causes the driver to wait for either the visible or clickability of a
    given element. Driver waits up to 30 seconds and then throws an error.
    Upon error, function returns, and other functions continue

    @params:
        wait_for - either the element to be 'visible' or 'clickable'
        search_by - a By.'' object, that enumerates what type our selector will be
        selector - an XPATH, css selector, ID, or other way to identify an HTML element
    @return: none
    """
    def _driver_wait(self, wait_for, search_by, selector, refresh):
        attempts = 0
        while (attempts < 5):
            if (wait_for == 'visible'):
                try:
                    WebDriverWait(self.driver,15).until(EC.visibility_of_element_located((search_by, selector)))
                    break
                except KeyboardInterrupt: 
                    sys.exit(1)
                except:
                    if refresh:
                        self.driver.refresh()
                        attempts = attempts + 1
            elif (wait_for == 'clickable'):
                try:
                    WebDriverWait(self.driver,15).until(EC.element_to_be_clickable((search_by, selector)))
                    break
                except KeyboardInterrupt:
                    sys.exit(1)
                except:
                    if refresh:
                        self.driver.refresh()
                        attempts = attempts + 1

    """
    _driver_wait(wait_for, search_by, selector)
    --------------
    Causes the driver to wait for either the visible or clickability of a
    given element. Driver waits up to 30 seconds and then throws an error.
    Upon error, function returns, and other functions continue

    @params:
        wait_for - either the element to be 'visible' or 'clickable'
        element - an element in the DOM, either the object itself, or
                    specified by (By.*,'selector') format
    @return: none
    """
    def _driver_wait_element(self, wait_for, element, refresh):
        attempts = 0
        while (attempts < 5):
            if (wait_for == 'visible'):
                try:
                    WebDriverWait(self.driver,15).until(EC.visibility_of_element_located(element))
                    break
                except KeyboardInterrupt: 
                    sys.exit(1)
                except:
                    if refresh:
                        self.driver.refresh()
                        attempts = attempts + 1
            elif (wait_for == 'clickable'):
                try:
                    WebDriverWait(self.driver,15).until(EC.element_to_be_clickable(element))
                    break
                except KeyboardInterrupt:
                    sys.exit(1)
                except:
                    if refresh:
                        self.driver.refresh()
                        attempts = attempts + 1


    """
    _click_element(search_by, selector)
    -----------------------------------
    Clicks the given element.

    @params:
        search_by - a By.'' object, that enumerates what type our selector will be
        selector - an XPATH, css selector, ID, or other way to identify an HTML element
    @return: none
    """
    def _click_element(self, search_by, selector, attempt_cap, refresh):
        stale = True
        attempts = 0
        while (stale and attempts < attempt_cap):
            if (refresh and attempts == attempt_cap - 1):
                self.driver.refresh()
                attempts = 0
            else:
                try:
                    if (search_by == By.CSS_SELECTOR):
                        self.driver.find_element_by_css_selector(selector).click()
                        stale = False
                    elif (search_by == By.XPATH):
                        self.driver.find_element_by_xpath(selector).click()
                        stale = False
                    elif (search_by == By.ID):
                        self.driver.find_element_by_id(selector).click()
                        stale = False
                    elif (search_by == By.LINK_TEXT):
                        self.driver.find_element_by_link_text(selector).click()
                        stale = False
                    elif (search_by == By.CLASS_NAME):
                        self.driver.find_element_by_class_name(selector).click()
                        stale = False
                    else:
                        print('Incorrect Parameters in the \'_click_element\' function. See documention.')
                except NoSuchElementException:
                    print('No such element found. Could not click ' + selector)
                    stale = False
                except StaleElementReferenceException:
                    stale = True
                    attempts = attempts + 1
                except ElementNotVisibleException:
                    attempts = attempts + 1



    """
    _click_element_no_selector(element)
    -----------------------------------
    Clicks the given element.

    @params: any element to be clicked (not an element)
    @return: none
    """
    def _click_element_no_selector(self, element, attempt_cap):
        print("entered _click_element_no_selector()")
        stale = True
        attempts = 0
        while(stale and attempts < attempt_cap):
            try:
                element.click()
                stale = False
            except NoSuchElementException:
                print('No such element found. Could not click')
                stale = False
            except StaleElementReferenceException:
                print("stale element")
                stale = True
                attempts = attempts + 1
                if (attempts == attempt_cap - 1):
                    self.driver.refresh()
                



    """
    _check_element_for_text(search_by, selector, text)
    --------------------------------------------------
    Checks a given element for a specific text.
    Returns a boolean indicating whether or not that text was found.

    @params:
        search_by - a By.'' object, that enumerates what type our selector will be
        selector - an XPATH, css selector, ID, or other way to identify an HTML element
        text - the text to be searched for
    @return: True if text was found; False otherwise
    """
    def _check_element_for_text(self, search_by, selector, text):
        count = 1
        while(count < 50):
            if re.search(text, self._get_element_text(search_by, selector)):
                return True
            count = count + 1
        return False



    """
    _get_element_text(search_by, selector)
    --------------------------------------
    Gets the text from a given element, and removes any non-ascii characters. Returns
    an empty string if there is no such element found. Otherwise, returns the text of
    the given element.

    @params:
        search_by - a By.'' object, that enumerates what type our selector will be
        selector - an XPATH, css selector, ID, or other way to identify an HTML element
    @return: the text from the specified element; empty string if error occured
    """
    def _get_element_text(self, search_by, selector):
        stale = True
        text = ""
        attempts = 0
        while(stale and attempts < 10):
            try:
                if (search_by == By.CSS_SELECTOR):
                    text = self._remove_non_ascii(self.driver.find_element_by_css_selector(selector).text)
                    stale = False
                elif (search_by == By.XPATH):
                    text = self._remove_non_ascii(self.driver.find_element_by_xpath(selector).text)
                    stale = False
                elif (search_by == By.ID):
                    text = self._remove_non_ascii(self.driver.find_element_by_id(selector).text)
                    stale = False
                elif (search_by == By.LINK_TEXT):
                    text = self._remove_non_ascii(self.driver.find_element_by_link_text(selector).text)
                    stale = False
                elif (search_by == By.CLASS_NAME):
                    text = self._remove_non_ascii(self.driver.find_element_by_class_name(selector).text)
                    stale = False
            except NoSuchElementException:
                stale = False
            except StaleElementReferenceException:
                stale = True
                attempts = attempts + 1

        return text



    """
    _get_element_text_no_selector(element)
    --------------------------------------
    Gets the text from a given element, and removes any non-ascii characters. Returns
    an empty string if there is no such element found. Otherwise, returns the text of
    the given element.

    @params: any element that you want the text of
    @return: the text from the specified element; empty string if error occured
    """
    def _get_element_text_no_selector(self, element):
        text = ''
        stale = True
        attempts = 0
        while(stale and attempts < 10):
            try:
                text = self._remove_non_ascii(element.text)
                stale = False
            except NoSuchElementException:
                stale = False
            except StaleElementReferenceException:
                stale = True
                attempts = attempts + 1

        return text



    """
    _check_element_exists(search_by, selector)
    ------------------------------------------
    Checks whether a given element exists. I'm actually not positive how this one works,
    but Tom used it, so I held onto it.

    @params:
        search_by - a By.'' object, that enumerates what type our selector will be
        selector - an XPATH, css selector, ID, or other way to identify an HTML element
    @return: none
    """
    def _check_element_exists(self, search_by, selector): 
        
        try:
            self.driver.implicitly_wait(0)
            self.driver.find_elements(search_by, selector)[len(self.driver.find_elements(search_by, selector)) - 1]
            self.driver.implicitly_wait(3)
        except NoSuchElementException:
            return False

        return True



    """
    _send_keys(search_by, selector, text)
    -------------------------------------
    Used to call the 'send_keys' operation on the driver. However, this
    function also double checks to make sure any text was fully entered
    into textboxes (compares it with the original string).

    @params:
        search_by - a By.'' object, that enumerates what type our selector will be
        selector - an XPATH, css selector, ID, or other way to identify an HTML element
        text - the text to be input using 'send_keys'
    @return: none
    """
    def _send_keys(self, search_by, selector, text):
        
        # inputs text to the given element
        self.driver.find_element(search_by, selector).send_keys(text)
        
        # that the text was input correctly
        while (self.driver.find_element(search_by, selector).get_attribute('value') != text):
            self.driver.find_element(search_by, selector).send_keys(Keys.CONTROL + 'a')
            self.driver.find_element(search_by, selector).send_keys(text)



    """
    _create_person()
    ----------------
    Creates an empty 'person' dictionary, that can be used to represent
    an individual in FamilySearch (or soon to be entered in FamilySearch).
    If you wish to add any aspects to this, make sure to add them following
    the appropriate heirarchy. (see 'birth' and 'name' for examples).

    @params: none
    @return: empty 'person' dictionary
    """
    def _create_person(self):
        person = {
            'hhid': '',
            'person_of_interest': '',
            'name': {
                'first': '',
                'last': ''
            },
            'fsid': '',
            'arkid': '',
            'gender': '',
            'birth': {
                'month': '',
                'year': '',
                'place': ''
            },
            'relation_to_head': '',
            'match_id': '',
            'match_score': '',
            'year_added': '',
            'ra': '',
            'county': self.county,
            'created_by': ''
        }
        return person



    """
    _print_person()
    ---------------
    Used mostly for development/debugging purposes. Prints all of the
    information of the currently stored person. Helps to make sure that 
    all data is stored correctly.

    @params: none
    @return: none
    """
    def _print_person(self):
        print("hhid: {}".format(self.person['hhid']))
        print("person_of_interest: {}".format(self.person['person_of_interest']))
        print("name: {0} {1}".format(self.person['name']['first'], self.person['name']['last']))
        print("fsid: {}".format(self.person['fsid']))
        print("arkid: {}".format(self.person['arkid']))
        print("gender: {}".format(self.person['gender']))
        if (self.person['birth']['month'] !=''):
            print("birth date: {0} {1}".format(self.person['birth']['month'], self.person['birth']['year']))
        else:
            print("birth date: {}").format(self.person['birth']['year'])
        print("birthplace: {}".format(self.person['birth']['place']))
        print("relation_to_head: {}".format(self.person['relation_to_head']))
        print("method: {}".format(self.person['method']))
        print("year_added: {}".format(self.person['year_added']))
        print("ra: {}".format(self.person['ra']))
        print("county: {}".format(self.person['county']))
   


    """
    _remove_non_ascii(text)
    -----------------------
    Removes any characters that you wouldn't find on a keyboard...
    pretty much (non-ascii characters)

    @params: String to be cleaned of non-ascii characters
    @return: Same string, with any non-ascii characters removed
    """
    def _remove_non_ascii(self, text):
        return ''.join(i for i in text if ord(i)<128)



    """
    _delete_person()
    ----------------
    Delete's the person associated with the given fsid
    
    @params: any fsid of someone to be removed (in string format)
    @return: none
    """
    def _delete_person(self, fsid):
        person_page = 'https://familysearch.org/tree/person/{}/details'
        self.driver.get(person_page.format(fsid))
        sleep(2)
        
        answer = input('Delete this person? (y/n): ')
        
        if(answer == 'y'):
            # click delete button
            self._click_element(By.CSS_SELECTOR, _PERSON_PAGE_DELETE_PERSON, 10, False)
            
            # text to input when deleting person
            text = 'Testing software, and I messed up'
            
            # fill out delete person page
            self._send_keys(By.CSS_SELECTOR, _DELETE_PAGE_TEXT_BOX, text)
            self._click_element(By.CSS_SELECTOR, _DELETE_PAGE_REVIEWED_BUTTON, 10, False)
            self._click_element(By.CSS_SELECTOR, _DELETE_PAGE_INCLUDED_STATEMENT_BUTTON, 10, False)
            self._click_element(By.CSS_SELECTOR, _DELETE_PAGE_DELETE_BUTTON, 10, False)



    """
    _write_person_added_to_tree()
    -----------------------------
    This function writes the current person that was added to the tree to
    a .csv file. This is a better method, because it writes one person at
    a time.
    
    """
    def _write_person_added_to_tree(self, fsid):
        j = open('people_added.csv', 'a')
        j.write(fsid + '\n')
        j.close()

    """
    _standardize(search_by, selector)
    ---------------------------------
    Standardizes the element associated with the selector (used when creating a person)

    @params:
        search_by - a By.'' object, that enumerates what type our selector will be
        selector - an XPATH, css selector, ID, or other way to identify an HTML element
    @return: none
    """
    def _standardize(self, search_by, selector):
        sleep(1)
        self.driver.find_element(search_by, selector).send_keys(Keys.ARROW_DOWN)
        sleep(.3)
        self.driver.find_element(search_by, selector).send_keys(Keys.ARROW_DOWN)
        self.driver.find_element(search_by, selector).send_keys(Keys.ENTER)



    """
    _standardize(search_by, selector)
    ---------------------------------
    Standardizes the element associated with the selector (used when creating a person)

    @params:
        search_by - a By.'' object, that enumerates what type our selector will be
        selector - an XPATH, css selector, ID, or other way to identify an HTML element
    @return: none
    """
    def _get_starting_point(self):
        lines = 0
        ra_id= ''
        
        if (os.path.isfile(self.outfile)):
            with open(self.outfile, 'r') as csvfile:
                reader = csv.reader(csvfile)
                for line in reader:
                    lines = lines + 1
                    
                    # stores the ra_id of each line (until the last line)
                    # the ra_id is on a different index in the outfile
                    ra_id = line[13]

        print(lines)
        return ra_id



    """
    _login()
    -------
    Given the stored username and password, this function loads the 
    selenium chromedriver and stores it in the CountyPrepper object
    as a local data member.

    @params: none (username/password from 'self')
    @return: none
    """
    def _login(self):
        # call chromedriver
        chromedriver = 'R:\\JoePriceResearch\\Python\\chromedriver.exe'
        os.environ['webdriver.chrome.driver'] = chromedriver
        self.driver = webdriver.Chrome('R:\\JoePriceResearch\\Python\\chromedriver.exe')

        # open Family Search and login
        self.driver.implicitly_wait(5) #seconds
        self.driver.get('https://familysearch.org/tree/#view=tree&section=pedigree')
        self._send_keys(By.NAME, 'userName', self.username)
        self._send_keys(By.NAME, 'password', self.password)
        self._click_element(By.ID, 'login', 10, False)
        sleep(2)





