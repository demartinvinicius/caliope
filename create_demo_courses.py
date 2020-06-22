MOODLE_TOKEN = "0402eb30801b04b2f47e9b65ae0efcdd"

import requests
import json
from datetime import datetime
from datetime import timedelta
import random
import html2text



""" This function creates a serie of courses to begin the test set
"""
def createcourses():
    baseurl = "https://platao.mindsforai.com/webservice/rest/server.php"

    dados2 = {
        "wstoken":MOODLE_TOKEN,
        "wsfunction":"core_course_create_courses",
        "moodlewsrestformat":"json",
        "courses[0][fullname]":"Mathematics",
        "courses[0][shortname]":"Mathematics",
        "courses[0][categoryid]": 1,
        "courses[1][fullname]":"Science",
        "courses[1][shortname]":"Science",
        "courses[1][categoryid]": 1,
        "courses[2][fullname]":"English",
        "courses[2][shortname]":"English",
        "courses[2][categoryid]": 1,
        "courses[3][fullname]":"Grammar",
        "courses[3][shortname]":"Grammar",
        "courses[3][categoryid]": 1,
        "courses[4][fullname]":"Art History",
        "courses[4][shortname]":"Art History",
        "courses[4][categoryid]": 1
        
        



    }

    r = requests.post(baseurl,data=dados2)

    print (r.text)
""" Function to retreive the courses stored at moodle
"""
def getcourses():
    #First we gonna take the list of existing courses
    baseurl = "https://platao.mindsforai.com/webservice/rest/server.php"
    dados = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "core_course_get_courses",
        "moodlewsrestformat":"json"
    }
    
    r = requests.post(baseurl,data = dados)
    print (r.text)
    dCourses = json.loads(r.text)
    return dCourses
    



""" Function to delete the existing courses to begin a very new set of examples
"""
def deletecourses():

    dCourses = getcourses()
    baseurl = "https://platao.mindsforai.com/webservice/rest/server.php"
    dados = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "core_course_delete_courses",
        "moodlewsrestformat":"json"
    }
    for course in dCourses:
        if course["id"] != 1:
            dados["courseids[0]"] = course["id"]
            r = requests.post(baseurl,data = dados)
            print(r.text)
        


def listevents():
    baseurl = "https://platao.mindsforai.com/webservice/rest/server.php"
    
    startday = int(datetime.timestamp(datetime.now()))
    endday = int(datetime.timestamp(datetime.now()+timedelta(days = 7)))
    dados = {
            "wstoken": MOODLE_TOKEN,
            "wsfunction": "core_calendar_get_action_events_by_courses",
            "moodlewsrestformat":"json",
            "courseids[0]": 7,
            "courseids[1]": 8,
            "courseids[2]": 9,
            "courseids[3]": 10,
            "courseids[4]": 11
        }
        
    r = requests.post(baseurl,data = dados)
    #print (r.text)


    #parsing events list
    dEves = json.loads(r.text)
    dEves2 = dEves["groupedbycourse"]
    
    
    #print(type(dEves2[0]))
    
    
    for i in range(0,len(dEves2)):
        
        
        
        #print (dEves2[i]["course"])
        events = dEves2[i]["events"]
        
        
        for event in events:
            print(event["course"]["fullname"])
            print(event["name"])
            print(html2text.html2text(event["description"]).strip())
            tStart = datetime.fromtimestamp(event["timestart"])
            print(tStart.strftime('%m/%d/%Y'))
        
        
def createevents():
    
    courseids = []
    dCourses = getcourses()
    
    for course in dCourses:
        if course["id"] != 1:
            courseids.append(course["id"])
    
    for i in range(1,30):
        #Choose id
        cid = courseids[random.randint(1,len(courseids)-1)]
        #Choose date
        currdatetime = datetime.today()
        print (str(currdatetime))
        newdate = currdatetime + timedelta(days = random.randint(5,60))
        print (str(newdate.date()))
        
        baseurl = "https://platao.mindsforai.com/webservice/rest/server.php"
        dados = {
            "wstoken": MOODLE_TOKEN,
            "wsfunction": "core_calendar_create_calendar_events",
            "moodlewsrestformat":"json",
            "events[0][name]":"Assessment"+str(i),
            "events[0][description]":"Assessment "+str(i),
            "events[0][courseid]":cid,
            "events[0][timestart]":int(datetime.timestamp(newdate)),
            "events[0][timeduration]":24*3600,
            "events[0][eventtype]":"course"
        }
        
        r = requests.post(baseurl,data = dados)
        
        print(r.text)
        
    
    
    
    
#getcourses()
listevents()
#resp = input("Would you like to delete existing courses?")
#if resp == "y" or resp == "Y":
#    deletecourses()
#resp = input("Would you like to create courses?")
#if resp == "y" or resp == "Y":
#    createcourses()
#resp = input("Would you like to create some calendar events?")
#if resp == "y" or resp == "Y":
#    createevents()