
Charts examples 
http://10.70.120.196:11000/asdash.html


About charts
http://www.pygal.org/en/latest/documentation/types/line.html




## Instalation

```
pip3 install -r pip_install_-r.txt
```

and run

```
circusd --daemon circus.marketing.ini
```


## Examples charts


#### Search by marker vm.israel from 2010-11-01 date

http://localhost:8888/rails_nano_aviasales/%0Aselect%20round(count(*)%20/%204)%20%20as%20searches,%20concat(o.name,%20%22(%22,%20o.iata,%20%22)%22)%20as%20origin,%20concat(d.name,%20%22(%22,%20d.iata,%20%22)%22)%20as%20destination%20%0Afrom%20rails_nano_aviasales.searches%20as%20s%20%0Ajoin%20rails_nano_aviasales.search_paramses%20as%20sp%20on%20sp.search_id%20=%20s.id%20join%20rails_nano_aviasales.places%20as%20o%20on%20sp.origin_id%20=%20o.id%20%0Ajoin%20rails_nano_aviasales.places%20as%20d%20on%20sp.destination_id%20=%20d.id%20%0Awhere%20s.creation_month%20%3E%20'2010-11-01'%20and%20s.marker%20=%20'vm.israel'%0Agroup%20by%20sp.origin_id,%20sp.destination_id%20%0Aorder%20by%20searches%20desc%20limit%2025%0A;?x=searches&type=table


