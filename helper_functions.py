# -*- coding: utf-8 -*-
"""
Created on Fri Apr 27 10:44:24 2018

@author: cookchr2
"""
import re
import sys
sys.path.append('R:/JoePriceResearch/Python/Anaconda3/Lib/site-packages')
from jellyfish import jaro_distance

'''
This File contains:
_parse_name - Parses a name to first, middle, last, and suffix.
_parse_date - Parses a date to day, month, and year.
_parse_place - Parses a place to city, county, state, and country.
_scorename - Gives a match score for a name.
_scoreevent - Gives a match score for event place and date.
'''

def _parse_name(self,name):
    '''
    Cleans the name to get it in the right format.
    
    name - Name to be parsed.
    '''
    # Trim the name.
    name = name.strip()
    
    # Initialize the values.
    firstname, middlename, lastname, suffix = ['']*4

    # Split the names of each person into first, middle, and last.
    # We take the first word up to a space as the firstname, the last
    # word after a space as the lastname, and anything in between as the middle.
    # Person of interest
    if name != '':
        # Clean out non-numeric characters.
        name = re.sub(r'[^\w ]+','',name)
        
        # Split the name at spaces.
        name = name.split(' ')
        
        # Get a suffix if one exists.
        if name[-1].lower().strip() in ['jr','sr','md','esquire','esq']:
            suffix = name[-1]
            del name[-1]
            
        # Eliminate a prefix if one exists.
        if len(name) > 0:
            if name[0].lower().strip() in ['doctor','dr','captain']:
                del name[0]

        # Assume that one name is a lastname.
        if len(name) == 1:
            lastname = name[0].strip()

        elif len(name) > 1:
            firstname = name[0].strip() 
            lastname = name[-1].strip()
        
        if len(name) > 2:
            # Loop to get all middle names.
            for x in range(1,len(name)-1):
                middlename = middlename + ' ' + name[x].strip()
            
            middlename = middlename.strip()
    
    # Strip and make lowercase.
    var = [firstname, middlename, lastname, suffix]
    for x in range(0,len(var)):
        var[x] = var[x].strip().lower()
            
    return var

def _parse_date(self,date):
    '''
    Cleans the date to get it in the right format.
    
    date - Date to be parsed.
    '''
    # Trim the date.
    date = date.strip()
    
    # Initialize the values.
    day, month, year = ['']*3
    
    # Make sure the date is not blank.
    if date != '':
        # Clean out unwanted characters.
        date = re.sub(r'[^A-Za-z0-9 ]+','',date)
        
        # Split the date.
        date = date.split()
        
        # We assume dd mmmm yyyy
        if len(date) > 2:
            day = date[0]
            month = date[1]
            year = date[2]
            
        elif len(date) == 2:
            month = date[0]
            year = date[1]
            
        elif len(date) == 1:
            year = date[0]
            
    # If the month says about, replace as missing.
    if month == 'about':
        month = ''
    
    # Make month 3 digit and lowercase.
    month = month[:3].strip().lower()
    
    # Strip year and day
    day = day.strip()
    year = year.strip()
    
    # Clean invalid years.
    if not re.search('[0-9][0-9][0-9][0-9]',year):
        year = ''
            
    return [day, month, year]

def _parse_place(self,place):
    '''
    Cleans the place to get it in the right format.
    
    place - Place to be parsed.
    '''
    # Trim the place.
    place = place.strip()
    
    # Initialize the values.
    city = ''
    county = ''
    state = ''
    country = ''
    # Make sure the place is not blank.
    if place != '':
        # Clean out unwanted characters.
        place = re.sub(r'[^A-Za-z,: ]+','',place)
        
        # Split the place on commas or colons.
        if re.search(r':',place):
            place = place.split(':')
        else:
            place = place.split(',')
            
        # We only handle standard dates, that is city, county, state, country.
        # Country is always last.
        country = place[-1]  # why are these number negative?
        
        if len(place) >= 4:
            city = place[-4]
            county = place[-3]
            state = place[-2]
        elif len(place) == 3:
            county = place[-3]
            state = place[-2]
        elif len(place) == 2:
            state = place[-2]
        elif len(place) == 1:
            states = ['alabama','alaska','arizona','arkansas','california','colorado','connecticut','delaware','florida','georgia','hawaii','idaho','illinois','indiana','iowa','kansas','kentucky','louisiana','maine','maryland','massachusetts','michigan','minnesota','mississippi','missouri','montana','nebraska','nevada','new hampshire','new jersey','new mexico','new york','north carolina', 'north dakota', 'ohio', 'oklahoma', 'oregon', 'pennsylvania', 'rhode island', 'south carolina', 'south dakota', 'tennessee', 'texas', 'utah', 'vermont', 'virginia', 'washington', 'west virginia', 'wisconson', 'wyoming']
            if place[0].lower() in states:
                state = place[0]
                country = 'United States'
    # Strip and make lowercase.
    var = [city, county, state, country]
    for x in range(0,len(var)):
        var[x] = var[x].strip().lower()
    return var
   
def _scoreevent(self,stype,masterdate,masterplace,fsdate,fsplace):
    '''
    This function gives a match score for event place and date.
    
    stype - This is a string describing what type of event is being matched.
    
    masterdate - First date.
    
    masterplace - First place.
    
    fsdate - Second date.
    
    fsplace - Second place.
    '''
    
    #Reset scoring varibales
    country, state, county, city, fscountry, fsstate, fscounty, fscity, day, month, year, fsday, fsmonth, fsyear = ['']*14
    score = [0,'']
    
    #Prep variables for matching
    #Master Varibles
    [city, county, state, country] = self._parse_place(masterplace)
    [day, month, year] = self._parse_date(masterdate)
    #Family Search Variables
    [fscity, fscounty, fsstate, fscountry] = self._parse_place(fsplace)
    [fsday, fsmonth, fsyear] = self._parse_date(fsdate)
    # Fix the place if fscountry is actually a state.
    if fscountry.upper() in ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", 'ALASKA', 'ARIZONA', 'ARKANSAS', 'CALIFORNIA', 'COLORADO', 'CONNECTICUT', 'DELAWARE', 'FLORIDA', 'GEORGIA', 'HAWAII', 'IDAHO', 'ILLINOIS', 'INDIANA', 'IOWA', 'KANSAS', 'KENTUCKY', 'LOUISIANA', 'MAINE', 'MARYLAND', 'MASSACHUSETTS', 'MICHIGAN', 'MINNESOTA', 'MISSISSIPPI', 'MISSOURI', 'MONTANA', 'NEBRASKA', 'NEVADA', 'NEW HAMPSHIRE', 'NEW JERSEY', 'NEW MEXICO', 'NEW YORK', 'NORTH CAROLINA', 'NORTH DAKOTA', 'OHIO', 'OKLAHOMA', 'OREGON', 'PENNSYLVANIA', 'RHODE ISLAND', 'SOUTH CAROLINA', 'SOUTH DAKOTA', 'TENNESSEE', 'TEXAS', 'UTAH', 'VERMONT', 'VIRGINIA', 'WASHINGTON', 'WASHINGTON D.C.', 'WEST VIRGINIA', 'WISCONSIN', 'WYOMING']:
        fscity = fscounty
        fscounty = fsstate
        fsstate = fscountry
        fscountry = 'united states'
    # Clean out 'city', 'county', or 'township'.
    city = re.sub(' [Cc]ity| [Tt]ownship| [Cc]ounty| [Ww]ard [0-9]+| \([^\)]+\)','',city)
    fscity = re.sub(' [Cc]ity| [Tt]ownship| [Cc]ounty| [Ww]ard [0-9]+| \([^\)]+\)','',fscity)
    county = re.sub(' [Cc]ity| [Tt]ownship| [Cc]ounty| [Ww]ard [0-9]+| \([^\)]+\)','',county)
    fscounty = re.sub(' [Cc]ity| [Tt]ownship| [Cc]ounty| [Ww]ard [0-9]+| \([^\)]+\)','',fscounty)
    if year != '' and fsyear != '':     
        try: #I know that this try loop seems silly, but this was breaking some code. So fix it I will!!!
            yeardiff = abs(int(year) - int(fsyear))
        except:
            yeardiff = 5
    else:
        yeardiff = 5
        
    #Give Synergetic Scores
    
    #Perfect match
    if day == fsday and month == fsmonth and year == fsyear and day != '' and month != '' and year != '':
        if city == fscity and county == fscounty and state == fsstate and country == fscountry and city != '' and county !='' and state != '' and country != '':
            score[0] = score[0] + 10
            score[1] = score[1] + stype + 'Perfect;'
        
        elif county == fscounty and state == fsstate and country == fscountry and county !='' and state != '' and country != '':
            score[0] = score[0] + 8
            score[1] = score[1] + stype + 'DateCSC;'
    
        elif state == fsstate and country == fscountry and state != '' and country != '':
            score[0] = score[0] + 6
            score[1] = score[1] + stype + 'DateSC;'
            
        else:
            score[0] = score[0] + 5
            score[1] = score[1] + stype + 'Date;'
    
    #Close match
    elif day == fsday and month == fsmonth and yeardiff <= 1  and day != '' and month != '' and year != '':
        if city == fscity and county == fscounty and state == fsstate and country == fscountry and city != '' and county !='' and state != '' and country != '':
            score[0] = score[0] + 8
            score[1] = score[1] + stype + 'CloseDateCCSC;'
        
        elif county == fscounty and state == fsstate and country == fscountry and county !='' and state != '' and country != '':
            score[0] = score[0] + 6
            score[1] = score[1] + stype + 'CloseDateCSC;'
    
        elif state == fsstate and country == fscountry and state != '' and country != '':
            score[0] = score[0] + 5
            score[1] = score[1] + stype + 'CloseDateSC;'

        else:
            score[0] = score[0] + 3.5
            score[1] = score[1] + stype + 'CloseDate;'

    #Month and Year
    elif month == fsmonth and year == fsyear and month != '' and year != '':
        if city == fscity and county == fscounty and state == fsstate and country == fscountry and city != '' and county !='' and state != '' and country != '':
            score[0] = score[0] + 7
            score[1] = score[1] + stype + 'MonthYearCCSC;'
        
        elif county == fscounty and state == fsstate and country == fscountry and county !='' and state != '' and country != '':
            score[0] = score[0] + 5
            score[1] = score[1] + stype + 'MonthYearCSC;'
    
        elif state == fsstate and country == fscountry and state != '' and country != '':
            score[0] = score[0] + 4
            score[1] = score[1] + stype + 'MonthYearSC;'

        else:
            score[0] = score[0] + 3
            score[1] = score[1] + stype + 'MonthYear;'

        
    #Month Close Year    
    elif month == fsmonth and yeardiff <= 1  and month != '' and year != '':
        if city == fscity and county == fscounty and state == fsstate and country == fscountry and city != '' and county !='' and state != '' and country != '':
            score[0] = score[0] + 6
            score[1] = score[1] + stype + 'M+-YearCCSC;'
        
        elif county == fscounty and state == fsstate and country == fscountry and county !='' and state != '' and country != '':
            score[0] = score[0] + 4
            score[1] = score[1] + stype + 'M+-YearCSC;'
    
        elif state == fsstate and country == fscountry and state != '' and country != '':
            score[0] = score[0] + 3
            score[1] = score[1] + stype + 'M+-YearSC;'

        else:
            score[0] = score[0] + 2
            score[1] = score[1] + stype + 'M+-Year;'

    #Year
    elif year == fsyear and year != '':
        if city == fscity and county == fscounty and state == fsstate and country == fscountry and city != '' and county !='' and state != '' and country != '':
            score[0] = score[0] + 6
            score[1] = score[1] + stype + 'YearCCSC;'
        
        elif county == fscounty and state == fsstate and country == fscountry and county !='' and state != '' and country != '':
            score[0] = score[0] + 4
            score[1] = score[1] + stype + 'YearCSC;'
    
        elif state == fsstate and country == fscountry and state != '' and country != '':
            score[0] = score[0] + 3
            score[1] = score[1] + stype + 'YearSC;'
            
        else:
            score[0] = score[0] + 2
            score[1] = score[1] + stype + 'Year;'
           
    #Near Year        
    elif yeardiff <= 1:
        if city == fscity and county == fscounty and state == fsstate and country == fscountry and city != '' and county !='' and state != '' and country != '':
            score[0] = score[0] + 5
            score[1] = score[1] + stype + '+-YearCCSC;'
        
        elif county == fscounty and state == fsstate and country == fscountry and county !='' and state != '' and country != '':
            score[0] = score[0] + 3
            score[1] = score[1] + stype + '+-YearCSC;'
    
        elif state == fsstate and country == fscountry and state != '' and country != '':
            score[0] = score[0] + 2
            score[1] = score[1] + stype + '+-YearSC;'
            
        else:
            score[0] = score[0] + 1
            score[1] = score[1] + stype + '+-Year;'
            
    else:
        if city == fscity and county == fscounty and state == fsstate and country == fscountry and city != '' and county !='' and state != '' and country != '':
            score[0] = score[0] + 3.5
            score[1] = score[1] + stype + 'CCSC;'
        
        elif county == fscounty and state == fsstate and country == fscountry and county !='' and state != '' and country != '':
            score[0] = score[0] + 2
            score[1] = score[1] + stype + 'CSC;'
    
        elif state == fsstate and country == fscountry and state != '' and country != '':
            score[0] = score[0] + 1
            score[1] = score[1] + stype + 'SC;'

    if country != fscountry and fscountry != '' and country != '':
        score[0] = score[0] - 2
        score[1] = score[1] + stype + 'WrongPlace;'
    
    if yeardiff > 10:
        score[0] = score[0] - 2
        score[1] = score[1] + stype + 'WrongYear;'

    return score
            

def _scorename(self,stype,mastername,fsname):
    '''
    This function will give a match score for a name.
    
    stype - This is a string describing what type of name it is.
    
    mastername - This is the first name to be matched.
    
    fsname - This is the second name to be matched.
    '''

    #Reset varibales        
    first, mid, last, suf, fsfirst, fsmid, fslast, fssuf = ['']*8
    score = [0,'']
    
    #Prep variables for matching
    [first, mid, last, suf] = self._parse_name(mastername)
    [fsfirst, fsmid, fslast, fssuf] = self._parse_name(fsname)
    
    #Make Jarowinkler scores (0 if missing)
    #First to first
    if first == '' or fsfirst =='':
        jw1 = 0
    else:
        jw1 = jaro_distance(first,fsfirst)
    
    #First to middle
    if first == '' or fsmid == '':
        jw2 = 0
    else:
        jw2 = jaro_distance(first,fsmid)
    
    #Middle to middle
    if mid == '' or fsmid == '':
        jw3 = 0        
    else:
        jw3 = jaro_distance(mid,fsmid)
    
    #Middle to first
    if mid == '' or fsfirst == '':
        jw4 = 0
    else:
        jw4 = jaro_distance(mid,fsfirst)

    #Last to last
    if last == '' or fslast == '':
        jw5 = 0
    else:
        jw5 = jaro_distance(last,fslast)
    
    #Do Synergetic Scoring (weights last name more)
    
    #If the last name matches, give scores
    if jw5 >= .9:
        if jw1 >= .9 and jw3 >= .9:
            score[0] = score[0] + 5
            score[1] = score[1] + stype + 'FullName;'
            
        elif jw2 >= .9 and jw4 >= .9: 
            score[0] = score[0] + 4
            score[1] = score[1] + stype + 'Inverted;'
    
        elif jw1 >= .9 and mid[:1] == fsmid[:1] and mid != '':
            score[0] = score[0] + 3.5
            score[1] = score[1] + stype + 'FullNameMidInitial;'
            
        elif jw1 >= .9:
            score[0] = score[0] + 3
            score[1] = score[1] + stype + 'FirstLast;'
            
        elif jw2 >= .9 or jw4 >= .9:
            score[0] = score[0] + 2.5
            score[1] = score[1] + stype + 'OneInvertedLast;'
            
        elif jw1 >= .8 and jw3 >= .8:
            score[0] = score[0] + 2
            score[1] = score[1] + stype + '-Full;'
            
        elif jw2 >= .8 and jw4 >= .8: 
            score[0] = score[0] + 1.5
            score[1] = score[1] + stype + '-Inverted;'
    
        elif jw1 >= .8 and mid[:1] == fsmid[:1] and mid != '':
            score[0] = score[0] + 1.5
            score[1] = score[1] + stype + '-FullNameMidInitial;'
    
        elif jw1 >= .8:
            score[0] = score[0] + 1.5
            score[1] = score[1] + stype + '-FirstLast;'
            
        elif jw2 >= .8 or jw4 >= .8:
            score[0] = score[0] + 1.5
            score[1] = score[1] + stype + '-OneInvertedLast;'
                        
        else:
            score[0] = score[0] + 1
            score[1] = score[1] + stype + 'Last;'
    

    #If the last name almost matches, give scores
    elif jw5 >= .8:
        if jw1 >= .9 and jw3 >= .9:
            score[0] = score[0] + 2.5
            score[1] = score[1] + stype + '-Full;'
            
        elif jw2 >= .9 and jw4 >= .9: 
            score[0] = score[0] + 2
            score[1] = score[1] + stype + 'Inverted-Last;'
            
        elif jw1 >= .9 and mid[:1] == fsmid[:1] and mid != '':
            score[0] = score[0] + 1.5
            score[1] = score[1] + stype + '-FullNameMidInitial;'
    
        elif jw1 >= .9:
            score[0] = score[0] + 1.5
            score[1] = score[1] + stype + 'First-Last;'
            
        elif jw2 >= .9 or jw4 >= .9: 
            score[0] = score[0] + 1.5
            score[1] = score[1] + stype + 'OneInverted-Last;'

        elif jw1 >= .8 and jw3 >= .8:
            score[0] = score[0] + 1
            score[1] = score[1] + stype + '-Full-Last;'
            
        elif jw2 >= .8 and jw4 >= .8: 
            score[0] = score[0] + 1
            score[1] = score[1] + stype + '-Inverted-Last;'
            
        elif jw1 >= .8 and mid[:1] == fsmid[:1] and mid != '':
            score[0] = score[0] + 1
            score[1] = score[1] + stype + '-Full-LastMidInitial;'
    
        elif jw1 >= .8:
            score[0] = score[0] + 1
            score[1] = score[1] + stype + '-First-Last;'

        elif jw2 >= .8 or jw4 >= .8:
            score[0] = score[0] + 1
            score[1] = score[1] + stype + '-OneInverted-Last;'
      
        else:
            score[0] = score[0] + .5
            score[1] = score[1] + stype + '-Last;'

    
    #If the last name does not match, give scores
    else:
        if jw1 >= .9 and jw3 >= .9:
            score[0] = score[0] + 1.5
            score[1] = score[1] + stype + 'FirMid;'
            
        elif jw2 >= .9 and jw4 >= .9: 
            score[0] = score[0] + 1
            score[1] = score[1] + stype + 'MidFir;'
            
        elif jw1 >= .9 and mid[:1] == fsmid[:1] and mid != '':
            score[0] = score[0] + 1
            score[1] = score[1] + stype + 'FirstMidInitial;'
    
        elif jw1 >= .9:
            score[0] = score[0] + 1
            score[1] = score[1] + stype + 'First;'
            
        elif jw2 >= .9 or jw4 >= .9: 
            score[0] = score[0] + 1
            score[1] = score[1] + stype + 'OneInverted;'
            
        elif jw1 >= .8 and jw3 >= .8:
            score[0] = score[0] + .5
            score[1] = score[1] + stype + '-FirMid;'
            
        elif jw2 >= .8 and jw4 >= .8: 
            score[0] = score[0] + .5
            score[1] = score[1] + stype + '-MidFir;'
            
        elif jw1 >= .8 and mid[:1] == fsmid[:1] and mid != '':
            score[0] = score[0] + 3.5
            score[1] = score[1] + stype + '-FirstMidInitial;'
    
        elif jw1 >= .8:
            score[0] = score[0] + .5
            score[1] = score[1] + stype + '-First;'
        
        elif jw2 >= .8 or jw4 >= .8:
            score[0] = score[0] + .5
            score[1] = score[1] + stype + '-OneInverted;'


    return score

