# coding=utf8
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url
from argparse import ArgumentParser
from tornado.httpclient import AsyncHTTPClient
import tornado.web
import tornado.gen
import tornado.concurrent
from urllib.parse import urlencode
from json import loads, dumps
from datetime import datetime
import pygal
from collections import OrderedDict
import logging

@tornado.gen.coroutine
def select(host, port, login, password, db, query):
    params = {
        'u': login,
        'p': password,
        'q': query
    }
    params = urlencode(params)
    url = "http://{host}:{port}/db/{db}/series?{params}".format(host=host, port=port, db=db, query=query, params=params)
    response = yield AsyncHTTPClient().fetch(url, method='GET', connection_timeout=60, request_timeout=120)
    return loads(response.body.decode('utf8'))[0]

def parse_response(response, x_column='time'):
    series = response.get('name', 'Unknown')
    columns = response['columns']
    points = reversed(response['points'])
    time = columns.index(x_column)
    tor = OrderedDict()
    point = None
    for point in points:
        values = {}
        for i, v in enumerate(point):
            values[columns[i]] = v
        tor[point[time]] =  values
    return series, reversed(list(filter(lambda c: c not in ('time', 'sequence_number', x_column), columns))), tor 

def options():
    parser = ArgumentParser()
    parser.add_argument("-o", "--host", dest="host", default="0.0.0.0", help="host to listen on")
    parser.add_argument("-p", "--port", dest="port", type=int, help="send json/udp messages to PORT", default=8888)
    parser.add_argument("-i", "--influx-host", dest="influx_host", help="influxdb host", default="localhost")
    parser.add_argument("-m", "--influx-port", dest="influx_port", help="influxdb port", default=8086, type=int)
    return parser.parse_args()

ops = options()

chart_types = {
    'line': pygal.Line,
    'bar': pygal.Bar,
    'stackedline': pygal.StackedLine,
    'stackedbar': pygal.StackedBar,
    'horizontalbar': pygal.HorizontalBar,
    'pie': pygal.Pie
}

class SvgHandler(RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, series, query):
        logging.info(query)
        x_axis = self.get_query_argument('x', 'time')
        chart = chart_types[self.get_query_argument('type', 'line')]
        time_format = self.get_query_argument('time_format', '%Y-%m-%d %H:%M:%S').replace('$', '%')
        self.set_header("Content-Type", 'image/svg+xml; вектор/хуектор')
        response = yield select(ops.influx_host, ops.influx_port, 'root', 'root', series, query)
        series, cols, rows = parse_response(response, x_axis)
        x_points = rows.keys()
        bar_chart = chart(x_label_rotation=45)
        bar_chart.title = self.get_query_argument('header', series)
        if x_axis == 'time':
            bar_chart.x_labels = list(map(lambda uts: datetime.fromtimestamp(uts / 1000).strftime(time_format), x_points))
        else:
            bar_chart.x_labels = x_points
        for col in cols:
            bar_chart.add(col, list(map(lambda x: rows[x][col], x_points)))
        self.write(bar_chart.render())
        self.finish()

logging.basicConfig(level=logging.DEBUG)
app = Application([
        url(r"/(.+?)/(.+)$", SvgHandler)
    ])
app.listen(ops.port)
IOLoop.current().start()
