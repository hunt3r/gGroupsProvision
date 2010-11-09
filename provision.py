# This file is part of gGroupsProv.
# gGroupsProv is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# gGroupsProv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with gGroupsProv.  If not, see <http://www.gnu.org/licenses/>.

# gGroupsProv was originally written by Chris Hunter <hunter.christopher@gmail.com>

import MySQLdb
import gdata.apps.groups.service
import re
import urllib
from xml.dom import minidom
import gsettings as gs
import time
import sys

#Begin Local Vars
gSettings=gs.getGoogleSettings()
dbSettings=gs.getDbSettings()
groups=gs.getGroups()
#Instantiate Google Apps service here                                                                                                                               
service=gdata.apps.groups.service.GroupsService(email=gSettings['g_email'], domain=gSettings['g_domain'], password=gSettings['g_pass'])
service.ProgrammaticLogin()
#End Local Vars

# validateEmail(string email)
# This is a utility to be sure we're dealing with a valid email address
def validateEmail(email):
    if len(email) > 6:
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
            return 1
        return 0

# compareStr(String str1, String str2)
# Simple string comparison
def compareStr(str1, str2):
    if str1 == str2:
        return 1
    else:
        return 0

# find(String str, List seq)
# Simple utility to see if a string exists in a List)
def find(str, seq):
    for item in seq:
        if compareStr(str,item): 
            return item

# groupExists(String groupId)
# See if a group exists in this google apps container
def groupExists(groupId):
    groupFound=0
    for group in service.RetrieveAllGroups():
        if compareStr(groupId.lower(), str(group['groupId']).lower()):
            groupFound=1
            print "Found group: %s"%(groupId)
    return groupFound

# purgeGroup(String groupId)
# If a group exists, delete it
def purgeGroup(groupId): 
    if groupExists(groupId):
        try:
            service.DeleteGroup(groupId)
            print "found and deleted: %s"%( group['groupId'])
        except Exception, err:
            print err

# addUserToGroup(String groupId, string email)
# Adds an email address to the specific group		
def addUserToGroup(groupId, email):
    try:
        service.AddMemberToGroup(email, groupId) 
        print "Adding %s to %s"%(email,groupId)
        return 1
    except Exception, err:
        print err
        return 0

# removeUserFromGroup(String groupId, string email)
# Removes an email from a giveng group
def removeUserFromGroup(groupId, email):
    try:
        service.RemoveMemberFromGroup(email, groupId)
        print "Removing %s from %s"%(email,groupId)
        return 1
    except Exception, err:
        print err
        return 0

# convertGroupMembersToDict(MemberFeed members)
# I had some trouble with doing lookups on this object, so I just made a quick dirty
# conversion to a standard List, and did it that way (probably a better way, please comment)
def convertGroupMembersToDict(members):
    memberDict=[]
    i=0
    for member in members:
        memberDict.append(member['memberId'].lower())
    print "%s emails found in this list"%(str(len(memberDict)))
    return memberDict

# getMembers(string groupId)
# A wrapper to add error handling to this call
def getMembers(groupId):
    try:
        return service.RetrieveAllMembers(groupId)
    except Exception, err:
        return err

# syncGroup(String groupId, List dbUsers)
# Compares what's found out on the cloud, with what we find in the database query
# If something is found in the cloud and not in the query, it's deleted
# If something is found in the database and not in the cloud, its added
def syncGroup(groupId, dbUsers):
    print "Syncing group %s"%(groupId)
    if groupExists("%s@%s"%(groupId, gSettings['g_domain'])):
        members=convertGroupMembersToDict(getMembers(groupId))
        #Add new users to the group
        print "Remove users not found database query from group"
        for member in members:
            if not find(member.lower(), dbUsers):            
              removeUserFromGroup(groupId, member)
        print "Done."
        print "Add users found in database, but not already in google group"
        #Remove users from the list that aren't in the datafeed anymore
        for email in dbUsers:
            #Probably a better way to search in the members collection here, kinda hacked it
            if not find(email, members):
              addUserToGroup(groupId, email)
        print "Done."

# addOwner(String grupId, String owner)
# makes a call to service to add an owner to the group
def addOwner(groupId, owner):
    try:
        #first we need to be sure this user is in the list
        addUserToGroup(groupId, owner)
        #sleep a second to be sure it's registered
        time.sleep(1)
        #Then we add them as an owner
        service.AddOwnerToGroup(owner, groupId)
        print "Adding %s as owner"%(owner)
    except Exception, err:
        print err

# addOwners(Dictionary group)
# Split the owner property, loop through list, add owners
def addOwners(group):
    for owner in group['owner'].split(','):
        if validateEmail(owner):
            addOwner(group['id'], owner)

# getListOfEmailsFromDb(Dictionary group)
# Creates a String List of email addresses from a database call defined in settings.xml          
def getListOfEmailsFromDB(group):
    #instantiate this dictionary
    emails=[]
    try:
        #instantiate connectiont ot MySQL
        db = MySQLdb.connect(host=dbSettings['db_host'], port=int(dbSettings['db_port']), user=dbSettings['db_user'], passwd=dbSettings['db_pass'], db=dbSettings['db'])
        cursor = db.cursor()
        #execute the query from the xml file
        cursor.execute(group['query'])
        #get emails from db query
        for row in cursor.fetchall():
        #if this is a valid email address, add it here
            if validateEmail(row[0]):
                emails.append(row[0].lower())
    except Exception, err:
        print err
        #return empty or partial set
        return emails
    finally:
        #clean up database connection
        db.close()
        #show some output
        print "Number of emails captured for %s: %d" %(group['id'], len(emails)) 
        return emails
    
# createGroup(Dictionary group)
# This checks to see if a group exists, then if not, creates it based on the group hash passed
def createGroup(group):
    try:
        if not groupExists("%s@%s"%(group['id'],gSettings['g_domain'])):
            print "Provisioning Group: %s"%(group['id'])
            service.CreateGroup(group['id'],"[%s] %s" % (group['permissions'],group['name']),group['description'], group['permissions'])    
            time.sleep(3) #need to sleep the thread for a few seconds so group becomes recognized
    except Exception,err:
        print err

# Main()
def main():
	try:
            #Kick off the loop
            for group in groups:
	    	try:
                    print "----------------------------------"
                    print "Starting %s "%(group['id'])
                    print "----------------------------------"
                    #Create the group if needed
                    createGroup(group)
                    #Sync emails existing and not existing
                    syncGroup(group['id'], getListOfEmailsFromDB(group))
                    #Add owners to the group
                    addOwners(group)
    		except Exception, err:
                    print err
	except Exception, outer_err:
            print outer_err
            print "This is likely caused by an error in your settings.xml"

#Kick off the app
if __name__ == '__main__':
	sys.exit(main())
