import logging
from functools import partial
import re
from json import dumps, load
from sys import argv
from os import stat
from time import sleep
from argparse import ArgumentParser, FileType
from socket import gethostname, socket, AF_INET, SOCK_DGRAM
from glob import glob
from functools import reduce
from signal import signal, SIGHUP

def multi_follow(masks, splitter="\n", interval=1, jump=True, follow=True):
    files = dict(map(lambda g: (g, dict(map(lambda path: (path, open(path, 'r')), glob(g)))), masks))
    files_count = reduce(lambda x,y: x + y, map(len, files.values()), 0)
    if jump:
        for _, flist in files.items():
            for file, fd in flist.items():
                fd.seek(stat(file).st_size)

    while True:
        no_data_count = 0
        for mask, file_list in files.items():
            for file, fd in file_list.items():
                try:
                    has = stat(file).st_size
                except:
                    next
                got = fd.tell()
                if got > has: #truncated file
                    fd.close()
                    file_list[file] = open(file, 'r')
                elif got < has:
                    # we can read line as two if read while full line is not written into file
                    data = fd.read(has - got)
                    for line in filter(lambda l: l != '', data.split(splitter)):
                        yield mask, file, line
                else: # got == has
                    no_data_count = no_data_count + 1
    
        if files_count == no_data_count:
            if follow:
                sleep(interval)
            else:
                exit(0)

def format_influx(message, pattern):
    m = [{
        "name": pattern['name'],
        "columns": list(message.keys()) + list(pattern['const'].keys()),
        "points": [list(message.values()) + list(pattern['const'].values())]
    }]
    return dumps(m).encode('utf8')

def options():
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", dest="config", help="read configuration from FILE", type=FileType('r'), metavar="FILE", default="logs.json")
    parser.add_argument("-t", "--target", dest="host", help="send json/udp messages to target HOST", metavar="HOST", default="localhost")
    parser.add_argument("-p", "--port", dest="port", type=int, help="send json/udp messages to PORT", metavar="PORT", default=4444)
    parser.add_argument("-j", "--jump", dest="jump", action="store_false", help="do not jump to the end of files at start", default=True)
    parser.add_argument("-f", "--follow", dest="follow", action="store_false", help="do not follow file", default=True)
    parser.add_argument("-r", "--dry-run", dest="dry", action="store_true", help="do not send messages, just dump them on console", default=False)
    args = parser.parse_args()
    config = load(args.config)
    return config, args.host, args.port, args.jump, args.follow, args.dry

def load_config(data):
    config = {}
    for path, patterns in data.items():
        config[path] = []
        for name, pattern in patterns.items():
            config[path].append({
                'pattern': re.compile(pattern['regexp']),
                'numeric_fields': pattern.get('numeric_fields', []),
                'name': name,
                'const': pattern.get('const', {}),
                'eval': dict(map(lambda e: (e[0], compile(e[1], '<config>', 'eval')), pattern.get('eval', {}).items()))
            })
    return config

logging.basicConfig(level=logging.DEBUG)

need_to_reload = False
def hup(f, s):
    global need_to_reload
    need_to_reload = True

signal(SIGHUP, hup)

hostname = gethostname()
while True:
    config, host, port, jump, follow, dry = options()
    patterns = load_config(config)
    target = socket(AF_INET, SOCK_DGRAM)
    sender = partial(logging.info, "%s %s") if dry else target.sendto
    
    for mask, path, line in multi_follow(patterns.keys(), jump=jump, follow=follow):
        if need_to_reload:
            need_to_reload = False
            break
        for pattern in patterns[mask]:
            match = pattern['pattern'].match(line)
            if match:
                message = match.groupdict()
                message['source'] = path.split('/')[-1]
                message['host'] = hostname
                for field in pattern['numeric_fields']:
                    message[field] = float(message[field])
                for field, code in pattern['eval'].items():
                    message[field] = eval(code, None, message)
    
                sender(format_influx(message, pattern), (host, port))
                break
