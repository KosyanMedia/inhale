bookmarks_load_callback({"metrics_first_events":"http://10.70.120.210:8686/metrics/select%20goal,%20count(goal)%20from%20metrics%20where%20time%20%3E%20now()%20-%201h%20and%20goal%20=~%20/%5Efirst/%20%20group%20by%20goal;?type=horizontalbar&x=goal","queues_send_time":"http://fuz3.int.avs.io:8888/yasen/select%20mean(duration)%20as%20avg_time,%20max(duration)%20as%20max_time,%20queue%20from%20queues%20where%20time%20%3E%20now()%20-%202h%20group%20by%20queue;?x=queue&type=bar","activations_count":"http://r2d2.int.avs.io:8888/retargeting/select activations_count from activations where time > now() - 4h;?show_legend=&x_label_rotation=60&q_time_format=","activations_exec_time":"http://r2d2.int.avs.io:8888/retargeting/select mean(exec_time), max(exec_time) from activations where time > now() - 4h group by time(30m);?show_legend=&fill=1&interpolate=cubic&q_time_format=$H","activations_select_time":"http://r2d2.int.avs.io:8888/retargeting/select mean(select_time), max(select_time) from activations where time > now() - 4h group by time(30m);?interpolate=cubic&legend_at_bottom=1&fill=1&x_label_rotation=30&q_time_format=$H:$M","cpu_mem_percentage":"http://r2d2.int.avs.io:8888/retargeting/select mean(mem_percent) as mem_usage_avg, max(mem_percent) as mem_usage_max, mean(cpu_percent) as cpu_avg, max(cpu_percent) as cpu_max from resources where time > now() - 8h group by time(30m);?interpolate=cubic&x_label_rotation=35&legend_at_bottom=1&q_time_format=$H:$M","requests_count":"http://r2d2.int.avs.io:8888/retargeting/select count(code) from requests where time > now() - 12h group by time(1h);?show_legend=&q_time_format=&fill=1","response_times":"http://r2d2.int.avs.io:8888/retargeting/select max(duration), mean(duration) from requests where time > now() - 1h group by time(5m);?interpolate=cubic&fill=1&x_label_rotation=30&q_time_format=$H:$M&show_legend=","retargeting_count":"http://r2d2.int.avs.io:8888/retargeting/select count(source) from retargeting where time > now() - 12h and shoot =~ /true/ group by time(1h);?show_legend=&interpolate=cubic&fill=1&x_label_rotation=30&q_time_format=$H:$M"});
