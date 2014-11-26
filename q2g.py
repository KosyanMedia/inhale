# coding=utf8
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url
from argparse import ArgumentParser
from tornado.httpclient import AsyncHTTPClient
import tornado.web
import tornado.gen
import tornado.concurrent
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
from json import loads, dumps
from datetime import datetime
import pygal
from collections import OrderedDict
import logging
from re import match
from pygal.style import *
from numbers import Number
from traceback import format_exception
from tornado.httpclient import HTTPError

@tornado.gen.coroutine
def select_influx(host, port, db, query, login='root', password='root', connect_timeout=60, request_timeout=120):
    params = {
        'u': login,
        'p': password,
        'q': query
    }
    params = urlencode(params)
    url = "http://{host}:{port}/db/{db}/series?{params}".format(host=host, port=port, db=db, query=query, params=params)
    response = yield AsyncHTTPClient().fetch(url, method='GET', connect_timeout=connect_timeout, request_timeout=request_timeout)
    raise tornado.gen.Return(loads(response.body.decode('utf8'))[0])

@tornado.gen.coroutine
def select_mysql(host, port, db, query, login='root', password='root', connect_timeout=60, request_timeout=120):
    import tornado_mysql
    conn = yield tornado_mysql.connect(host=host, port=port, user=login, passwd=password, db=db)
    cur = conn.cursor()
    yield cur.execute('set names utf8;')
    cur.close()
    cur = conn.cursor()
    yield cur.execute(query)
    points = []
    for row in cur:
        toa = []
        points.append(toa)
        for val in row:
            if isinstance(val, datetime):
                val = val.timestamp()
            elif isinstance(val, Number):
                val = float(val)
            toa.append(val)

    tor = {
        'name': query,
        'columns': list(map(lambda c: c[0], cur.description)),
        'points': points
    }
    cur.close()
    conn.close()
    raise tornado.gen.Return(tor)

@tornado.gen.coroutine
def select_pgsql(host, port, db, query, login=None, password=None, connect_timeout=60, request_timeout=120):
    import psycopg2
    import momoko
    DSNL = 'dbname={db} user={login} password={password} host={host} port={port}'
    DSN = 'dbname={db} host={host} port={port}'
    DSNL = 'dbname={db} host={host} port={port}'
    pool = momoko.Pool(
        dsn=(DSNL if login else DSN).format(db=db, login=login, password=password, host=host, port=port),
        size=1
    )
    cur = yield momoko.Op(pool.execute, query)
    points = []
    for row in cur:
        toa = []
        points.append(toa)
        for val in row:
            if isinstance(val, datetime):
                val = val.timestamp()
            elif isinstance(val, Number):
                val = float(val)
            toa.append(val)

    tor = {
        'name': query,
        'columns': list(map(lambda c: c[0], cur.description)),
        'points': points
    }
    raise tornado.gen.Return(tor)


def parse_response(response, x_column='time', options={}):
    series = response.get('name', 'Unknown')
    columns = response['columns']
    points = response['points']
    time = columns.index(x_column)
    tor = OrderedDict()
    point = None

    if options.get('transpose'):
        transpose_col = options['transpose']
        new_columns = []
        new_points = OrderedDict()

        for point in points:
            values = {}
            for i, v in enumerate(point):
                values[columns[i]] = v
            time = values.pop(x_column)
            transpose_col_name = values.pop(transpose_col)
            if time not in new_points:
                new_points[time] = {}
            for k in values:
                colname = transpose_col_name + '_' + k
                new_points[time][colname] = values[k]
                if colname not in new_columns:
                    new_columns.append(colname)
        for ts in new_points:
            for col in new_columns:
                if col not in new_points[ts]:
                    new_points[ts][col] = 0
        return series, new_columns, new_points

    for point in points:
        values = {}
        for i, v in enumerate(point):
            values[columns[i]] = v
        tor[point[time]] =  values
    return series, list(filter(lambda c: c not in ('time', 'sequence_number', x_column), columns)), tor

def options():
    parser = ArgumentParser()
    parser.add_argument("-o", "--host", dest="host", default="0.0.0.0", help="host to listen on")
    parser.add_argument("-p", "--port", dest="port", type=int, help="port to listen on", default=8888)
    parser.add_argument("-i", "--db-host", dest="db_host", help="influxdb host", default="localhost")
    parser.add_argument("-m", "--db-port", dest="db_port", help="influxdb port", default=8086, type=int)
    parser.add_argument("-d", "--db-type", dest="db_type", help="influx/mysql/pgsql", default="influx")
    parser.add_argument("-l", "--db-login", dest="db_login", help="database login", default="root")
    parser.add_argument("-s", "--db-password", dest="db_password", help="database password", default="root")
    return parser.parse_args()

ops = options()

chart_types = {
    'line': pygal.Line,
    'bar': pygal.Bar,
    'stackedline': pygal.StackedLine,
    'stackedbar': pygal.StackedBar,
    'horizontalbar': pygal.HorizontalBar,
    'pie': pygal.Pie,
    'gauge': pygal.Gauge,
    'dot': pygal.Dot
}

select = {
    'influx': select_influx,
    'mysql': select_mysql,
    'pgsql': select_pgsql
}[ops.db_type]

def render_trace(tp, val, trace):
    html_escape = lambda x: x.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    head = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600"><rect width="100%" height="100%" fill="#ff5722"></rect>'
    tail = '</svg>'
    stack_lines = format_exception(tp, val, trace)
    stack= ''.join(list(map(lambda e: '<text x="5" y="' + str(e[0] * 20) + '" font-size="12">' + html_escape(e[1]) + '</text>', enumerate(stack_lines, 1))))
    ex_type = '<text x="180" y="20" font-size="14">' + html_escape(str(tp)) + '</text>'
    if isinstance(val, HTTPError) and val.response:
        ex_type = ex_type + ''.join(map(lambda v: '<text xml:space="preserve" font-size="14" x="5" y="' + str(len(stack_lines) * 20 + v[0] * 18 + 30)+ '" font-family="monospace">' + html_escape(v[1] )+ '</text>', enumerate(val.response.body.decode('utf8').split('\n'), 1)))
    return head + stack + ex_type + tail

TABLE_HEAD="""<html><head>
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load("visualization", "1", {packages:["TYPE"]});
      google.setOnLoadCallback(function(){
        var options = {};
        var data = new google.visualization.DataTable();"""
TABLE_TAIL="""
       var table = new google.visualization.TYPE(document.getElementById('t'));
        table.draw(data, options);
      });
    </script>
</head><body><div id="t"></div></body></html>"""

def render_google_chart(cols, rows, chart_type='table',options={}):
    tor = TABLE_HEAD.replace('TYPE', chart_type)
    cols = list(cols)
    if chart_type == 'gauge':
        cols = cols[1:]
    col_type = 'string' if chart_type == 'table' else 'number'
    tor = tor + '\n'.join(map(lambda r: 'data.addColumn("{}", "{}");'.format(col_type, r or ''), cols))
    data = []
    def stringer(x):
        if x:
            if isinstance(x, float) and round(x) == x:
                x = int(x)
            return str(x)
        else:
            return ''
    for k in rows.keys():
        norm = stringer if chart_type == 'table' else float
        data.append(list(map(lambda c: norm(rows[k][c]), cols)))
    tor = tor + "data.addRows(" + dumps(data) + ");"
    for o in options.keys():
        if o == 'sortColumn':
            tor = tor + 'options["' + str(o) + '"] = ' + str(options[o]) + ';';
        else:
            tor = tor + 'options["' + str(o) + '"] = "' + str(options[o]) + '";';
    tor = tor + TABLE_TAIL.replace('TYPE', chart_type.capitalize())
    return tor

MAP_HEAD="""
<html>
<head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
         <link rel="stylesheet" href="http://cdn.leafletjs.com/leaflet-0.7.3/leaflet.css" />
        <style>.iata{{}}</style>
</head>
<body>
        <div id="map" style="width: 100%; height: 100%"></div>
        <script src="http://cdn.leafletjs.com/leaflet-0.7.3/leaflet.js"></script>
        <script>
                var map = L.map('map', {{zoomControl: false}}).setView([{center}], {zoom});
                L.tileLayer(
                    'http://{{s}}.tile.osm.org/{{z}}/{{x}}/{{y}}.png',
                     {{
                        id: 'examples.map-i875mjb7',
                        detectRetina: true
                     }}
                ).addTo(map);
"""

MAP_POPUP="""
                L.marker([{coords}], {{icon: L.divIcon({{className: "iata", html: "{iata}", }})}}).addTo(map);
"""

MAP_LINE="""
                L.polyline([
                        [{orig_coords}],
                        [{dest_coords}]
                ], {{
                    color: 'red',
                    weight: 0.006 * {searches},
                    opacity: 0.003 * {searches}
                }}).addTo(map);
"""

MAP_TAIL="""
        </script>
</body>
</html>
"""

def render_map(cols, rows, chart_type,options={}):
    tor = [MAP_HEAD.format(**options)]
    iatas = {}
    for l, r  in rows.items():
        if 'fix_coords' in options:
            r['orig_coords'] = ','.join(reversed(r['orig_coords'].split(':')))
            r['dest_coords'] = ','.join(reversed(r['dest_coords'].split(':')))
        tor.append(MAP_LINE.format(**r))
        if r['orig'] not in iatas:
            iatas[r['orig']] = True
            tor.append(MAP_POPUP.format(coords=r['orig_coords'], iata=r['orig']))
        if r['dest'] not in iatas:
            iatas[r['dest']] = True
            tor.append(MAP_POPUP.format(coords=r['dest_coords'], iata=r['dest']))
    tor.append(MAP_TAIL.format(**options))
    return ''.join(tor)

class SvgHandler(RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, series, query):
        logging.info(query)
        font = self.get_argument('font_family', 'Helvetica')
        secondary = self.get_argument('secondary', '').split(',')
        sparkline = self.get_argument('sparkline', False)
        chart_type = self.get_argument('type', 'line')
        time_format = self.get_argument('time_format', '%Y-%m-%d %H:%M:%S').replace('$', '%')
        self.set_header("Content-Type", 'image/svg+xml' if chart_type not in ('table','gauge', 'map') else 'text/html')
        try:
            response = yield select(ops.db_host, ops.db_port, series, query, login=ops.db_login, password=ops.db_password)
            x_axis = self.get_argument('x', 'time')
            options = {
                'transpose': self.get_argument('transpose', False)
            }
            series, cols, rows = parse_response(response, x_axis, options)
            x_points = list(rows.keys())
            style = DefaultStyle
            style.font_family = font
            chart_params = {};
            for name in self.request.arguments:
                if name not in ('type', 'x', 'time_format', 'secondary', 'sparkline'):
                    value = self.get_argument(name)
                    if name == 'style':
                        value = globals()[value]
                        value.font_family = font
                    elif name == 'range':
                        value = sorted(list(map(float, value.split(','))))
                    elif match(r"^[\d-]+$", value):
                        value = int(value)
                    chart_params[name] = value
            if x_axis == 'time':
                x_labels = reversed(list(map(lambda uts: datetime.fromtimestamp(uts / 1000).strftime(time_format), x_points)))
            else:
                x_labels = list(map(str, x_points))

            if chart_type in ('table', 'gauge'):
                self.write(render_google_chart([x_axis] + list(cols), rows, chart_type=chart_type, options=chart_params))
            elif chart_type == 'map':
                self.write(render_map([x_axis] + list(cols), rows, chart_type=chart_type, options=chart_params))
            else:
                chart = chart_types[chart_type]
                bar_chart = chart(**chart_params)
                bar_chart.x_labels = x_labels
                for col in cols:
                    points = list(map(lambda x: rows[x][col], x_points))
                    if col in secondary:
                        bar_chart.add(col, points, secondary=True)
                    else:
                        bar_chart.add(col, points)
                self.write(bar_chart.render_sparkline() if sparkline else bar_chart.render())
        except:
            tp, value, traceback = sys.exc_info()
            self.write(render_trace(tp, value, traceback))
        finally:
            self.finish()

logging.basicConfig(level=logging.DEBUG)
app = Application([
        url(r"/(.+?)/(.+)$", SvgHandler)
    ])
app.listen(ops.port)
IOLoop.current().start()
