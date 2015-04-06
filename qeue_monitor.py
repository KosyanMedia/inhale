from json import loads
from urllib.request import urlopen
from time import sleep
import logging

hosts = ['fuz3', 'fuz4', 'fuz5', 'fuz6', 'fuz7']
while True:
  result = []
  for h in hosts:
    try:
      res = urlopen('http://' + h + '.int.avs.io:4401/status')
      data = loads(res.read().decode('utf8'))
      messages = 0
      for k, v in data.items():
        messages += v['messages']

      result.append(str(messages))
    except:
      result.append('0')
  print(','.join(hosts + result))
  sleep(1)
