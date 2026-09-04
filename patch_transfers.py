import requests

def test_transfers():
    res = requests.get('https://fantasy.premierleague.com/api/entry/4211029/transfers/')
    print(res.json())

test_transfers()
