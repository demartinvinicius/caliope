FACEBOOK_TOKEN = "EAAG0YYVksEIBAOnP7IIKHSx6ZAyTRCZBDeYGiCTBEv3STAkEkGIuYbE10g3u3duoMkzbZAAKdWnb5ozvgL0sbIc1gS1MJrEE37U9LMZAFb2uLdqCCqcZCIx3rPbM2LieZBbboEeJOgi2HS0IPxCMmmQMuXtjPYtODWX82xmwxiNAZDZD"


import requests

url = "https://graph.facebook.com/v7.0/me/messenger_profile?access_token=" + FACEBOOK_TOKEN

dados = {
    "get_started": {
        "payload": "payload do get starded {{user_full_name}}"
    },
    "greeting": [
        {
            "locale": "default",
            "text": "Welcome {{user_full_name}} - I'm Calíope and I'm gonna help you with your studies"
        }
    ],
    "persistent_menu": [
        {
            "locale": "default",
            "call_to_actions": [
                {
                    "type": "postback",
                    "title": "Talk to Calíope as a Student",
                    "payload": "student"
                },
                {
                    "type": "web_url",
                    "title": "Access Moodle",
                    "url": "https://platao.mindsforai.com"
                }
            ]
        }
    ]
}

header = {
    "Content-type": "application/json"
}

r = requests.post(url,headers = header,json=dados)

print(r.text)