VERIFY_TOKEN = "b13005af8a09c91a9c0406c870caceba57feb90947e2f6e4d84076345cc31c96"
FB_PAGE_TOKEN = "EAAG0YYVksEIBAMXcIZC3rpD5T2T4vgOVHQIe7u4ziwZBvPaoelHezJEDRuc99nFwSXshbhJ7ZBf8TjCRwXsbFxa3ZBHi3RLjgQZBiJBQ185fiOHigTOrIs6djgKHLAHAUcqw8ZB3KRdoK9UZCij5hofi26SR2W1XJMZCG8rmmfTcjgZDZD"


import sys
import json
import base64
import requests
import boto3




def lambda_handler(event, context):
    # TODO implement
    
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
        
        
        print ("### Mensagem recebida ###")
        print (dctMess)
        
        for entry in dctMess["entry"]:
            print ("## Entrei no laco entry ##")
            print ("## Time=" + str(entry["time"]) + " ##")
            print ("## PageId=" + entry["id"] + " ##")
            for msg in entry["messaging"]:
                sSenderId = msg["sender"]
                sSenderId = sSenderId["id"]
                print("# Sender=" + sSenderId + " #")
                sReceiveId = msg["recipient"]
                sReceiveId = sReceiveId["id"]
                print("# Receive=" + sReceiveId + " #")
                
                print("# Timestamp=" + str(msg["timestamp"]) + " #")
                
                dTheMsg = msg["message"]
                
                if "text" in dTheMsg:
                    #We have a text message
                    print("# Texto da Mensagem=" + dTheMsg["text"] + " #")
                if "attachments" in dTheMsg:
                    #We have a attachment!
                    for atach in dTheMsg["attachments"]:
                        if atach["type"] == "audio":
                            dPayload = atach["payload"]
                            sUrl = dPayload["url"]
                            
                            print("# Precisamos processar o arquivo=" + sUrl + " #")
                            
                            arq = requests.get(sUrl, allow_redirects=True, stream=False)
                            
                            bDados = bytearray()
                            
                            for chunk in arq.iter_content(255):
                                if chunk:
                                    bDados += chunk
                            
                            bs64 = str(base64.b64encode(bDados),'utf-8')

                            print("# Tipo arquivo: "+arq.headers["content-type"])
                            print("# O arquivo foi convertido para base 64 #")

                            
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
                            
                            r = requests.post("https://speech.googleapis.com/v1p1beta1/speech:recognize?key=AIzaSyDjfBNT79HnO9fyTPXUbeRy6TPms7zvBcg",json = datum,headers = headers)
                            
                            print(r.json())
                            
                            sJsonresp = json.dumps(r.json())
                            
                            print(sJsonresp)
                            
                            dict = json.loads(sJsonresp)
                            
                            if "results" in dict:
                                for rst in dict["results"]:
                                    print(rst["languageCode"])
                                    for alt in rst["alternatives"]:
                                        print(alt["transcript"])
                                        dRetorno = {
                                            "recipient": {
                                                "id": sSenderId
                                            },
                                            "message": {
                                                "text": alt["transcript"]
                                            }
                                        }
                                        sUrlRetorno = "https://graph.facebook.com/me/messages?access_token=" + FB_PAGE_TOKEN
                                        requests.post(sUrlRetorno,json = dRetorno)
                                    alt0 = rst["alternatives"][0]
                                    polly_client = boto3.client("polly")
                                    response = polly_client.synthesize_speech(VoiceId='Camila',
                                       OutputFormat='mp3', 
                                       Text = alt0["transcript"])
                                    
                                    
                                    file = open('/tmp/speech.mp3', 'wb')
                                    file.write(response['AudioStream'].read())
                                    file.close()
                                    
                                    dRet2 = {
                                        "recipient": json.dumps({"id":sSenderId}),
                                        "message": json.dumps({"attachment":{"type":"audio","payload":{"is_reusable": True}}})
                                    }
                                    
                                    strdados = json.dumps(dRet2)
                                    print("*****  "+strdados)
                                    
                                    dadosfile = {'filedata': ('speech.mp3',open('/tmp/speech.mp3','rb'),'audio/mpeg')}
                                    resp = requests.post(sUrlRetorno,data = dRet2,files = dadosfile)
                                    
                                    print(resp.json())
                            
                            

        print ("### Final da Mensagem ###")
        
        
        
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