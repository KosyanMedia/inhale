from json import dumps

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

def render(cols, rows, chart_type='table',options={}):
    tor = TABLE_HEAD.replace('TYPE', chart_type)
    cols = list(cols)
    if chart_type == 'gauge':
        cols = cols[1:]
    if chart_type == 'table':
        nums = options.get('numbers', '').split(',')
        col_type = lambda name: 'number' if name in nums else 'string'
    else:
        col_type = lambda: 'number'
    tor = tor + '\n'.join(map(lambda r: 'data.addColumn("{}", "{}");'.format(col_type(r), r or ''), cols))
    data = []
    def stringer(x, n):
        if x:
            if n in nums:
                return int(x)
            elif isinstance(x, float) and round(x) == x:
                x = int(x)
            return str(x)
        else:
            return ''
    for k in rows.keys():
        norm = stringer if chart_type == 'table' else float
        data.append(list(map(lambda c: norm(rows[k][c], c), cols)))
    tor = tor + "data.addRows(" + dumps(data) + ");"
    for o in options.keys():
        if o == 'sortColumn':
            tor = tor + 'options["' + str(o) + '"] = ' + str(options[o]) + ';';
        else:
            tor = tor + 'options["' + str(o) + '"] = "' + str(options[o]) + '";';
    tor = tor + TABLE_TAIL.replace('TYPE', chart_type.capitalize())
    return tor
