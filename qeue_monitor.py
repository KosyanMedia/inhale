from json import loads
from urllib.request import urlopen
from time import sleep
import logging

hosts = ['fuz3', 'fuz4', 'fuz5', 'fuz6', 'fuz7']
while True:
  for h in hosts:
    try:
      res = urlopen('http://' + h + '.int.avs.io:4401/status')
      data = loads(res.read().decode('utf8'))
      messages = 0
      subscriptions = 0
      for k, v in data.items():
        messages += v['messages']
        subscriptions += v['subscriptions']

      print(','.join([h, str(messages), str(subscriptions)]))
    except:
      print('error')
  sleep(1)

