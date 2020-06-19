"""
This code gets some csv files and train a Wit Robot
"""

WIT_SERVER_TOKEN = "JUEFOUOWZIKGTKBZQEQU4H3QHGOWFL5D"

import csv
import requests
import json

def CriaEntity(entityname):
    payload = {
        "name": entityname,
        "roles": []
    }
    header = {
        "Authorization":"Bearer "+WIT_SERVER_TOKEN
    }
    url = "https://api.wit.ai/entities?v=20200513"
        
    r = requests.post(url,headers=header,json=payload)
    
    print(r)    


def RecordKeyWords(currententity,row):
    url = "https://api.wit.ai/entities/"+currententity+"/keywords?v=20200513"
    payload = {
        "keyword": row[0]
    }
    syns = []
    row.pop(0)
    
    for syn in row:
        if syn != "":
            syns.append(syn)
            
    payload["synonyms"] = syns
    header = {
        "Authorization":"Bearer "+WIT_SERVER_TOKEN
    }
    r = requests.post(url,headers=header,json=payload)
    
    print(r)    
    


def EntitiesTraining():
    with open("/home/ec2-user/environment/caliope/Entities.CSV",newline='') as csvfile:
        reader = csv.reader(csvfile,delimiter=";")
    
        firstrow = next(reader,None)
    
        print (firstrow)
        row1 = next(reader,None)
    
        #Grava a primeira entity
        currententity = row1[0]
        CriaEntity(row1[0])    
    
    
        row1.pop(0)
        RecordKeyWords(currententity,row1)
    
    
        for row in reader:
            if currententity != row[0]:
                CriaEntity(row[0])
                currententity = row[0]
            row.pop(0)
            RecordKeyWords(currententity,row)


def IntentsTraining():
    with open("/home/ec2-user/environment/caliope/Intents.CSV",newline='') as csvfile:
        reader = csv.reader(csvfile,delimiter=";")
    
        firstrow = next(reader,None)
        print(firstrow)
        
        header = {
            "Authorization": "Bearer "+WIT_SERVER_TOKEN,
            "Content-Type": "application/json"
        }

        url = "https://api.wit.ai/intents?v=20200513"
        for row in reader:
            payload = {
                "name": row[0]
            }
            
            
            r = requests.post(url,headers = header,json = payload)
            print (r)


def UtterancesTraining():
    with open("/home/ec2-user/environment/caliope/Utterances.CSV",newline='') as csvfile:
        reader = csv.reader(csvfile,delimiter=";")
    
        firstrow = next(reader,None)
        print(firstrow)
        
        header = {
            "Authorization": "Bearer "+WIT_SERVER_TOKEN,
            "Content-Type": "application/json"
        }

        url = "https://api.wit.ai/utterances?v=20200513"
        for row in reader:
            payload = {
                "text": row[0],
                "intent": row[5],
                "entities": [
                ],
                "traits":[
                    ]
            }
            if row[1] != "":
                
                if "$" in row[1]:
                    ent = {
                        "entity": row[1] + ":datetime"
                    }
                else:
                    ent = {
                        "entity": row[1] + ":" + row[1]
                    }
                if row[2] != "":
                    ent["start"] = int(row[3])
                    ent["end"] = int(row[4])
                    ent["body"] = row[2]
                    ent["entities"] = []
                payload["entities"].append(ent)
            
            payarray = [payload]    
            r = requests.post(url,headers = header,json = payarray)
            print (r.text)



resp = input("Would you like to train entities (y/n)?")
if resp == 'y' or resp=="Y":
    EntitiesTraining()
resp = input("Would you like to train intents (y/n)?")
if resp == 'y' or resp == "Y":
    IntentsTraining()
resp = input("Would you like to train Utterances (y/n)?")
if resp == 'y' or resp == "Y":
    UtterancesTraining()


            
        
