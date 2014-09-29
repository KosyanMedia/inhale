import logging
import psutil
from json import dumps
from time import time, sleep
from sys import argv
from glob import glob
from argparse import ArgumentParser, FileType
from socket import socket, AF_INET, SOCK_DGRAM
from functools import partial

def delta(name, current_value, cache={}, process=None):
    current_stamp = time()
    key = ''.join((str(process.pid), '_', name)) if process else name
    if key in cache:
        last_stamp, last_value = cache[key]
    else:
        last_stamp, last_value = process.create_time() if process else psutil.boot_time(), 0
    cache[key] = (current_stamp, current_value)
    return (current_value - last_value) / (current_stamp - last_stamp)

def deltas(counters, process=None, prefix=None):
    return dict(map(lambda c: (''.join((prefix, '_', c[0])) if prefix else c[0], delta(c[0], c[1], process=process)), counters.items()))

def proc_data(p, name):
    cpu = lambda p:deltas(p.cpu_times()._asdict(), process=p, prefix='cpu')
    cpup = lambda p:{'cpu_percent': p.cpu_percent()}
    io = lambda p:deltas(p.io_counters()._asdict(), process=p, prefix='io')
    ctx = lambda p:deltas(p.num_ctx_switches()._asdict(), process=p, prefix='ctx')
    mem = lambda p:dict(map(lambda i: ('mem_' + i[0], i[1]), p.memory_info_ex()._asdict().items()))
    tor = {'name': name}
    for call in (cpu, cpup, io, ctx, mem):
        tor.update(call(p))
    return tor

def sys_data():
    cpu = lambda: dict(map(lambda a: ('cpu_' + str(a[0]), a[1]), enumerate(psutil.cpu_percent(percpu=True))))
    mem = lambda: dict(map(lambda a: ('mem_' + str(a[0]), a[1]), psutil.virtual_memory()._asdict().items()))
    def disk():
        tor = {}
        for hdd, info in psutil.disk_io_counters(perdisk=True).items():
            for k, v in info._asdict().items():
                tor['hdd_' + hdd + '_' + k] = v
        return tor
    
    tor = {}
    #for call in (cpu, mem, disk):
    for call in (cpu, mem):
        tor.update(call())
    return tor

def processes(pts):
    for pid_files in pts:
        for pid_file in glob(pid_files):
            f = open(pid_file, 'r')
            try:
                process = psutil.Process(int(f.read().replace("\n", "")))
                yield pid_file, process
            except:
                pass
            finally:
                f.close()
   
def format_influx(message, name):
    m = [{
        "name": name,
        "columns": list(message.keys()),
        "points": [list(message.values())]
    }]
    return dumps(m).encode('utf8')

def options():
    parser = ArgumentParser()
    parser.add_argument("-s", "--source", dest="source", help="load pids from files")
    parser.add_argument("-t", "--target", dest="host", help="send json/udp messages to target HOST", metavar="HOST", default="localhost")
    parser.add_argument("-p", "--port", dest="port", type=int, help="send json/udp messages to PORT", metavar="PORT", default=4444)
    parser.add_argument("-r", "--dry-run", dest="dry", action="store_true", help="do not send messages, just dump them on console", default=False)
    args = parser.parse_args()
    return args.host, args.port, args.dry, args.source

logging.basicConfig(level=logging.DEBUG)
host, port, dry, pid_paths = options()
target = socket(AF_INET, SOCK_DGRAM)
sender = partial(logging.info, "%s %s") if dry else target.sendto

while True:
    sender(format_influx(sys_data(), 'resources'), (host, port))
    for path, proc in processes(pid_paths.split(',')):
        name = path.split('/')[-1]
        try:
            sender(format_influx(proc_data(proc, name), 'processes'), (host, port))
        except:
            pass
    sleep(5)
