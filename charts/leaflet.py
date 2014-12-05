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

def render(cols, rows, chart_type,options={}):
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
