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

import sys
import json
import base64
import requests
import boto3


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
        reply = {
            "messageto": sSenderId,
            "text": "Thanks you've send " + dTheMsg["text"]
        }
        sendtextback(reply)
        
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
                    handle_facebook_message(msg)

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