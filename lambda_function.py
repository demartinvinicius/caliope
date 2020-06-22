""" Lambda function that receives incomings messages from Facebook - Webhook
This Lambda is attached to a AWS API that receives the Http Call from Facebook.
Facebook call this service in 2 ways:
First One - Using GET Method - This kind happens when Facebook register the Webhook
In this case Facebook pass a VERIFY_TOKEN that we must verify if identical to the one declared in this file
After that we repply with a "challenge" that Facebook sends along the GET resquest to register our function

Second One - This is called when the Page receives a message and it's handled by this module too.
In this case the calling use the POST method"""




VERIFY_TOKEN = "b13005af8a09c91a9c0406c870caceba57feb90947e2f6e4d84076345cc31c96"
FB_PAGE_TOKEN = "EAAG0YYVksEIBAMXcIZC3rpD5T2T4vgOVHQIe7u4ziwZBvPaoelHezJEDRuc99nFwSXshbhJ7ZBf8TjCRwXsbFxa3ZBHi3RLjgQZBiJBQ185fiOHigTOrIs6djgKHLAHAUcqw8ZB3KRdoK9UZCij5hofi26SR2W1XJMZCG8rmmfTcjgZDZD"
GOOGLE_KEY = "AIzaSyDjfBNT79HnO9fyTPXUbeRy6TPms7zvBcg"
WIT_SERVER_TOKEN = "JUEFOUOWZIKGTKBZQEQU4H3QHGOWFL5D"
MOODLE_TOKEN = "0402eb30801b04b2f47e9b65ae0efcdd"


import sys
import json
import base64
import requests
import boto3
import html2text
from datetime import datetime
from datetime import timedelta

""" Main entry point - Verifys the method used for calling and invokes the right method to use
"""
def lambda_handler(event, context):

    #First - We're gonna see if we have a GET or POST method
    try:
        dctReqContext = event["requestContext"]
        dctHttp = dctReqContext["http"]
        
        if dctHttp["method"] == "GET":
            return handle_get(event)
        if dctHttp["method"] == "POST":
            return handle_post(event)
            
    except:
        return {
            'statusCode': 200,
            'body': "exception"
        }

""" Process the GET Method of the HTTP Request
This means that Facebook wants to authenticate the webhook
"""

def handle_get(event):
    try:
        dctQueryParameters = event["queryStringParameters"]
        if dctQueryParameters["hub.mode"] != "subscribe":
            response = "Invalid Formart"
        elif dctQueryParameters["hub.verify_token"] != VERIFY_TOKEN:
            response = "Invalid Token"
        else:
            response = dctQueryParameters["hub.challenge"]
    except:
        response = "Exception!"
    finally:
        httpresp = {
            'statusCode': 200,
            'body': response
        }   
        
    return httpresp



""" Handles the google response to audio transcript
google_response is the json replied by google after the audio transcript

returns a dict with the transcript and the confidence of the response
if google can't trascribe return a empty string for the transcript and a confidence of 0.0
"""
def handle_google(google_response):
    sJsonresp = json.dumps(google_response)

    dictx = json.loads(sJsonresp)
    if "results" in dictx:
        
        print("#|# Resposta Google #!# " + sJsonresp + " #!#")
        rst = dictx["results"][0]
            
        alt0 = rst["alternatives"][0]
            
        result = {
            "transcript": alt0["transcript"],
            "confidence": alt0["confidence"]
        }
        
    
    else:
        result = {
            "transcript": "",
            "confidence": 0.0
        }
        
    return result

""" Handles audio inputs from Facebook
sUrl is a URL that links the audio file sended by Facebook
returns a dict with the transcript and the confidence of the response
if google can't trascribe return a empty string for the transcript and a confidence of 0.0
"""
def handle_audio(sUrl):
    print("#|# Arquivo de Audio #|#" + sUrl + " #|#")
                            
    arq = requests.get(sUrl, allow_redirects=True, stream=False)
                            
    bDados = bytearray()
                            
    for chunk in arq.iter_content(255):
        if chunk:
            bDados += chunk
                        
    bs64 = str(base64.b64encode(bDados),'utf-8')

    #print("# Tipo arquivo: "+arq.headers["content-type"])
    #print("# O arquivo foi convertido para base 64 #")

                            
    #Prepara a configuração para processamento do Google
    datum = {
        'config': {
            "maxAlternatives": 3,
            "alternativeLanguageCodes": ["en-US"],
            "enableAutomaticPunctuation": True,
            "encoding": "MP3",
            "languageCode": "pt-BR",
            "model": "default",
            "sampleRateHertz": 44100
        },
        'audio': {
            'content': bs64        
        }
    }
                            
    headers = {'Content-Type': 'application/json; charset=utf-8'}
                            
    r = requests.post("https://speech.googleapis.com/v1p1beta1/speech:recognize?key="+GOOGLE_KEY,json = datum,headers = headers)
    
    resp = handle_google(r.json())
    
    return resp    

""" This function sends a text back to the sender of the message
"""
def sendtextback(textmessage):
    dRetorno = {
        "recipient": {
            "id": textmessage["messageto"]
        },
        "message": {
            "text": textmessage["text"]
        }
    }
    sUrlRetorno = "https://graph.facebook.com/me/messages?access_token=" + FB_PAGE_TOKEN
    requests.post(sUrlRetorno,json = dRetorno)
    
    return None

""" This function sends a audio back to the sender of the message
"""
def send_audio_back(msg):
    polly_client = boto3.client("polly")
    response = polly_client.synthesize_speech(VoiceId='Joanna',
        OutputFormat='mp3', 
        Text = msg["text"])

    file = open('/tmp/speech.mp3', 'wb')
    file.write(response['AudioStream'].read())
    file.close()
                                    
    dRet2 = {
        "recipient": json.dumps({"id":msg["messageto"]}),
        "message": json.dumps({"attachment":{"type":"audio","payload":{"is_reusable": False}}})
    }
    
    #strdados = json.dumps(dRet2)
    #print("*****  "+strdados)

    dadosfile = {'filedata': ('speech.mp3',open('/tmp/speech.mp3','rb'),'audio/mpeg')}
    sUrlRetorno = "https://graph.facebook.com/me/messages?access_token=" + FB_PAGE_TOKEN
    requests.post(sUrlRetorno,data = dRet2,files = dadosfile)
    
    #print(resp.json())

    return None

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



def GetNextAssessments():
    baseurl = "https://platao.mindsforai.com/webservice/rest/server.php"
    moodlecourses = [11,10,9,8,7]

    dados = {
            "wstoken": MOODLE_TOKEN,
            "wsfunction": "core_calendar_get_action_events_by_courses",
            "moodlewsrestformat":"json"
        }
        
    i = 0
    for courseid in moodlecourses:
        s1 = f"courseids[{i}]"
        dados[s1]=courseid
        i += 1
    
    startday = int(datetime.timestamp(datetime.now()))
    dados["timesortfrom"] = startday
    
    r = requests.post(baseurl,data = dados)


    repply = "\n"
    dEves = json.loads(r.text)
    dEves2 = dEves["groupedbycourse"]
    
    
    for i in range(0,len(dEves2)):
        
        
        
        
        
        
        
        events = dEves2[i]["events"]
        currcourse = ""
        for event in events:
            
            if currcourse != event["course"]["fullname"]:
                repply += "On "+event["course"]["fullname"]+".\n"
                currcourse = event["course"]["fullname"]
            
            repply += html2text.html2text(event["description"]).strip()
            repply += " on "
            tStart = datetime.fromtimestamp(event["timestart"])
            repply += tStart.strftime('%m/%d - at %I:%M%p - %A')
            repply += ".\n"


                    
        #repply += "On course "+curcourse["displayname"]+" "
        #repply += f"I've found {iNumcourses} assessments \n"
    
        #for event in dEvents["events"]:
        #repply += html2text.html2text(event["description"]).strip()
        #repply += ".\n"
        #tStart = datetime.datetime.fromtimestamp(event["timestart"])
        #repply += "On "
        #repply += tStart.strftime('%m/%d - at %I:%M%p - %A')
        #epply += ".\n"



    return repply



""" This function process a text message with the help of Wit.AI
    Receives a string of text
    Returns a text processed
"""
def handle_text_withai(dTexto):
    
    
    
    sTexto = dTexto["text"]
    
    params = {
        "v": "20200513",
        "q": sTexto
    }

    headers = {
        "Authorization": "Bearer "+WIT_SERVER_TOKEN
    }
    sUrl = "https://api.wit.ai/message"
    
    r = requests.get(sUrl,headers = headers,params=params)
    
    # Let's see if was identified at least an intend...
    resp = json.loads(r.text)
    dIntents = resp["intents"]
    
    if len(dIntents) == 0:
        return "I'm sorry I can't understand what do you intent...\nMay you reformultate your question?"
    else:
        print(r.text)
        #Now we gonna take a list of courses on moodle
        #May we gonna need to filter the information by course
        #moodlelist = getcourses()
        
        
        repply =  "Ok! I understood that your intent is "
        if dIntents[0]["name"] == "NextAssessment":
            repply += "to get the next assessments.\n"
        
        #repply += " with a confidence of "+str(dIntents[0]["confidence"])
        dEntities = resp["entities"]
        if len(dEntities) > 0:
            print(r.text)
            repply += "\nIn your message I've found "+str(len(dEntities))+" entity(ies):"
            print(repply)
            
            kej = dict.keys(dEntities)
            for kejk in kej:
                entiti = dEntities[kejk][0]
                print(type(entiti))
                print(entiti)
                #repply += "\n"+entiti["name"]+" "+entiti["body"]+" "+entiti["value"]
        
            
                    
        
        if dIntents[0]["name"] == "NextAssessment":
            
            fastmsg = {
                "text": "Just a momment. I'm looking for information.",
                "messageto": dTexto["messageto"]
            }
            
            sendtextback(fastmsg)
            send_audio_back(fastmsg)
            
            
            repply += GetNextAssessments()

        return repply
    

""" This function handles the call when there is a new MESSAGE to process
"""
def handle_facebook_message(msg):
                    
    sSenderId = msg["sender"]
    sSenderId = sSenderId["id"]
    #print("# Sender=" + sSenderId + " #")
    sReceiveId = msg["recipient"]
    sReceiveId = sReceiveId["id"]
    #print("# Receive=" + sReceiveId + " #")
                
    #print("# Timestamp=" + str(msg["timestamp"]) + " #")
    
    dTheMsg = msg["message"]
                
    #Does we have a text message
    if "text" in dTheMsg:
        #reply = {
        #    "messageto": sSenderId,
        #    "text": "Thanks you've send " + dTheMsg["text"]
        #}
        
        #Let's process the text message....
        dDataToHandle = {
            "messageto": sSenderId,
            "text": dTheMsg["text"]
        }
        
        
        reply = {
            "messageto": sSenderId,
            "text": handle_text_withai(dDataToHandle)
        }
        sendtextback(reply)
        send_audio_back(reply)
        
    if "attachments" in dTheMsg:
        #We have a attachment!
        for atach in dTheMsg["attachments"]:
            if atach["type"] == "audio":
                dPayload = atach["payload"]
                sUrl = dPayload["url"]
                spoke = handle_audio(sUrl)
                if spoke["confidence"]>0.5:
                    reply = {
                        "messageto": sSenderId,
                        "text": "I've understood " + spoke["transcript"] + ". Rigth?"
                    }
                    
                else:
                    reply = {
                        "messageto": sSenderId,
                        "text": "I'm so sorry. But I didn't understand! Could you repeat?"
                    }
                    
                send_audio_back(reply)    
    return None










""" This function gets a course list from Moodle"""
def get_moodle_course_list():
    baseurl = "https://platao.mindsforai.com/webservice/rest/server.php"
    
    dados = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "core_course_get_courses",
        "moodlewsrestformat":"json"
    }
    
    r = requests.post(baseurl,data = dados)
    dCourses = json.loads(r.text)
    
    strReply = "Let's see what I have here:\nI have found the following courses in my memory."
    for course in dCourses:
        if course["id"] != 1:
            strReply += "\n" + course["displayname"]+"."
    
    strReply += "\nWith me you can get information about: next assessments, next activities and grades!"
    strReply += "\nI hope that you enjoy talking to me!"
    strReply += "\nThank you for your attention"+"."
        
    
    
    return strReply



def handle_post(event):
    try:
        
        if event["isBase64Encoded"]:
            body = str(base64.b64decode(event['body']),encoding='utf-8')
        else:
            body = event['body']
        
        
        dctMess = json.loads(body)
        
        if dctMess["object"] != "page":
            return {
                'statusCode': 200,
                'body': "Formato não reconhecido"
            }
        
        
        print ("#|# Facebook Message #|# " + json.dumps(dctMess) + " #|#")

        for entry in dctMess["entry"]:
            #print ("## Time=" + str(entry["time"]) + " ##")
            #print ("## PageId=" + entry["id"] + " ##")
            
            # Is it really a message that we received?
            if "messaging" in entry:
                for msg in entry["messaging"]:
                    if "message" in msg:
                        # We received a facebook message
                        handle_facebook_message(msg)
                    
                    if "postback" in msg:
                        dctSender = msg["sender"]
                        if msg["postback"]["payload"] == "student":
                            sCoursesList = get_moodle_course_list()
                            textmessage = {
                    
                                "messageto": dctSender["id"],
                                "text": sCoursesList
                            }

                            sendtextback(textmessage)
                            send_audio_back(textmessage)

        return {
            'statusCode': 200,
            #'headers': {
            #    'content-type': "application/json" 
            #},
            'body': "Obrigado"
        }
    except:
        
        resp = str(sys.exc_info()[0])
        print (resp)
        return {
            'statusCode': 200,
            'body': "Exception=" + resp
        }      