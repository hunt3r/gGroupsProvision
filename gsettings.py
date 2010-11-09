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

from xml.etree import ElementTree as ET
import os

#Get the xml file
xmlFile = os.path.abspath(__file__)
xmlFile = os.path.dirname(xmlFile)
#change this if you want to change the default xml filename
xmlFile += "/settings.xml"

#Parse the XML file into a an ElementTree
try:
    tree = ET.parse(xmlFile)
except Exception, inst:
    print "Error opening XML file %s: %s" % (xmlFile, inst)

# returnNodeText
# Utility method to return the text value of an xml node or a default if not found
# Returns String
def returnNodeText(node, default):
    try:
        if node != None:
            return node.text
        else:
            return default
    except Exception, inst:
        print "Error with XML node %s in returnNodeText(): %s" % (node, inst)

# getDbSettings
# This parses the root ElementTree into a hashtable of settings values
# for the MySQL database
# Return Hashtable
def getDbSettings():
    #traverse the xml file (albeit simplistically)
    root = tree.getroot()
    settings = root.find('settings')
    database = settings.find('database')
    db_user=returnNodeText(database.find('db_user'), 'DefaultUser')
    db_pass=returnNodeText(database.find('db_pass'),'DefaultPass')
    db_host=returnNodeText(database.find('db_host'),'DefaultHost')
    db=returnNodeText(database.find('db'),'DefaultDb')
    db_port=returnNodeText(database.find('db_port'),3306)
    settingsHash= {'db_user':db_user,'db_pass':db_pass,'db_host':db_host,'db':db,'db_port':db_port}
    return settingsHash

# getGoogleSettings()
# Same as getDbSettings, only gets google apps info from XML file
# Return Hashtable
def getGoogleSettings():
    #tree = ET.parse(xmlFile)
    root = tree.getroot()
    settings = root.find('settings')
    google = settings.find('googleapps')
    g_user=returnNodeText(google.find('g_user'), 'DefaultUser')
    g_pass=returnNodeText(google.find('g_pass'),'DefaultPass')
    g_domain=returnNodeText(google.find('g_domain'),'DefaultDomain')
    settingsHash= {'g_user':g_user,'g_pass':g_pass,'g_domain':g_domain,'g_email':"%s@%s"%(g_user,g_domain)}
    return settingsHash

# cleanString()
# simple utility method to remove illegal characters from a list ID
def cleanString(str):
    illegals=[' ', '%', '@', '$', '^', '"', "'",'&','*']
    for i in illegals:
        str=str.replace(i, "-")
    return str

# getGroups()
# get a list of hashtables of all group data needed to create a google group
# from a mysql datasource.
def getGroups():
    grpList=[]
    root = tree.getroot()
    groups = root.find('groups')
    for group in  groups.findall('group'):
        id=group.find('id')
        perms=group.find('permissions')
        name=group.find('name')
        desc=group.find('description')
        owner=group.find('owner')
        query=group.find('query')
        groupHash={'id':cleanString(id.text),'permissions':perms.text,'name':name.text,'description':desc.text,'owner':owner.text,'query':query.text}
        grpList.append(groupHash)
    return grpList


