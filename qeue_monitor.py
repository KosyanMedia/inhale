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
      for k, v in data.items():
        print(','.join([h, k, str(v['messages']), str(v['subscriptions'])]))
    except:
      print('error')
  sleep(1)
