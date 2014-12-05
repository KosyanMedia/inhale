JSGAUGE="""<html><head>
<script src="//cdn.jsdelivr.net/justgage/1.0.1/justgage.min.js"></script>
<script src="//cdn.jsdelivr.net/raphael/2.1.2/raphael-min.js"></script>
<script>
function run(){{
  var options = {{
    id: 'g',
    startAnimationTime: 1,
    levelColorsGradient: false
  }};
  {ops};
  new JustGage(options);
}};</script>
</head><body onload="run()">
<div id='g' style='width: 100%; height: 100%;'></div>
</body></html>"""

def render(col, rows, chart_type,options={}):
    for l, r  in rows.items():
        ops = 'options["value"] = ' + str(r[col]) + ';'
    ops = ops + ';'.join(map(lambda i: 'options["' + i[0] + '"] = "' + str(i[1]) + '"', options.items()))
    return JSGAUGE.format(ops=ops)
