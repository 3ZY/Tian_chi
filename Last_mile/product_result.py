# !/usr/bin/python
# coding:utf-8

import csv
import math
import operator
import copy

C_time_hh_max = '20'
C_time_hh = '08'
C_time_mi = '00'
C_speed = 15 # km/h
C_serv = 3
C_serv_fix = 5
C_load = 140
C_cheat = 10
C_penalty_tw = 5
C_penalty_base = 10
C_man=1000

def getmins(time_str):
	hh = time_str.split(':')[0]
	mi = time_str.split(':')[1]
	return (int(hh)-int(C_time_hh))*60+int(mi)-int(C_time_mi)
def dist(longi1, lati1, longi2, lati2):
	if longi1 is None or lati1 is None or longi2 is None or lati2 is None:
		return None
	else:
		delta_lati = (lati1 - lati2) / 2
		delta_longi = (longi1 - longi2) / 2
		tmp_val = math.sin(math.radians(delta_lati)) ** 2 + \
        	math.cos(math.radians(lati1)) * \
        	math.cos(math.radians(lati2)) * \
        	math.sin(math.radians(delta_longi)) ** 2
	return int(round(2 * math.asin(math.sqrt(tmp_val)) * 6378137 / (C_speed*1000/60)))
def serv(num_ord):
	return round(C_serv*math.sqrt(num_ord)+5) if num_ord>0 else 0

# ---------- loading original data ------------
# -- note: '1.csv','2.csv','3.csv','4.csv','5.csv' are the files we provide, please put the files in the correct path!
points={}
#网点
site_points = set()
csvfile = open('1.csv','rU')
lines = csv.reader(csvfile)
for line in lines:
	sInd,lng,lat = line
	if lng=='Lng':
		continue
	site_points.add(sInd)
	points.setdefault(sInd,[])
	points[sInd].extend([float(lng),float(lat)])
csvfile.close()
#配送点
spot_points=set()
csvfile = file('2.csv','rU')
lines = csv.reader(csvfile)
for line in lines:
	sInd,lng,lat = line
	if lng=='Lng':
		continue
	spot_points.add(sInd)
	points.setdefault(sInd,[])
	points[sInd].extend([float(lng),float(lat)])
csvfile.close()
#商家
shop_points=set()
csvfile = file('3.csv','rU')
lines = csv.reader(csvfile)
for line in lines:
	sInd,lng,lat = line
	if lng=='Lng':
		continue
	shop_points.add(sInd)
	points.setdefault(sInd,[])
	points[sInd].extend([float(lng),float(lat)])
csvfile.close()
#电商包裹
f_orders={}
f_spot_oid={}
site_spots={}
csvfile = file('4.csv','rU')
lines = csv.reader(csvfile)
for line in lines:
	oid,tInd,fInd,num_ord = line
	if num_ord=='Num':
		continue
	f_orders.setdefault(oid,[])
	f_orders[oid].extend([tInd,fInd,getmins('08:00'),getmins('20:00'),int(num_ord)])
	f_spot_oid[tInd]=oid
	site_spots.setdefault(fInd,[])
	site_spots[fInd].append(tInd)
csvfile.close()
#O2O包裹
e_orders={}
e_spot_oids={}
shop_spots={}
csvfile = file('5.csv','rU')
lines = csv.reader(csvfile)
for line in lines:
	oid,tInd,fInd,tw_1,tw_2,num_ord = line
	if tw_1=='Pickup_time':
		continue
	e_orders.setdefault(oid,[])
	e_spot_oids.setdefault(tInd,[])
	e_orders[oid].extend([tInd,fInd,getmins(tw_1),getmins(tw_2),int(num_ord),2])
	e_spot_oids[tInd].extend([oid])
	shop_spots.setdefault(fInd,set())
	shop_spots[fInd].add(tInd)
csvfile.close()


site_spots_dis={} #网点对应的配送点距离
site_spot_spots_dis={} #网点下各配送点之间的距离
for site,spots in site_spots.items():
	site_spots_dis.setdefault(site,{})
	site_spot_spots_dis.setdefault(site,{})
	for spot in spots:
		site_spots_dis[site].setdefault(spot,0)
		site_spots_dis[site][spot]=dist(points[site][0],points[site][1],points[spot][0],points[spot][1])
		site_spot_spots_dis[site].setdefault(spot,{})
		for spot2 in spots:
			if spot2==spot:
				continue
			site_spot_spots_dis[site][spot].setdefault(spot2,0)
			site_spot_spots_dis[site][spot][spot2]=dist(points[spot][0],points[spot][1],points[spot2][0],points[spot2][1])


# ---------- 电商订单 algorithm ------------
site_cost={} #网点耗时
site_paths={} #网点下的节约表路径
site_paths_cost={} #网点下路径及耗时

for site in site_points:
	#初始化网点耗时
	site_cost[site]=0xffffffff

	#节约法建表
	spots=site_spots[site]
	table={} #节约表
	for i in range(len(spots)):
		for j in range(i+1,len(spots)):
			if site_spots_dis[site][spots[i]]+site_spots_dis[site][spots[j]]-site_spot_spots_dis[site][spots[i]][spots[j]]>0:
				table[spots[i]+','+spots[j]]=site_spots_dis[site][spots[i]]+site_spots_dis[site][spots[j]]-site_spot_spots_dis[site][spots[i]][spots[j]]
	#节约法路径
	site_paths.setdefault(site,[])
	used_spots=[]#已经用配送点
	spot_path_no={}#配送点所在路径编号
	now_path_num=0 #路径数
	for spot,dis in sorted(table.items(),key=operator.itemgetter(1),reverse=True):
		spot1,spot2=spot.split(',')
		if (spot1 in used_spots) and (spot2 in used_spots):
			if used_spots.count(spot1)==2 or used_spots.count(spot2)==2:
				continue
			if spot1 not in site_paths[site][spot_path_no[spot2]][0]:
				now_load=sum([ f_orders[f_spot_oid[val]][4] for val in set(site_paths[site][spot_path_no[spot1]][0]) ])
				now_load+=sum([ f_orders[f_spot_oid[val]][4] for val in set(site_paths[site][spot_path_no[spot2]][0]) ])
				if now_load<=C_load:
					site_paths[site][spot_path_no[spot1]].append([spot1,spot2])
					site_paths[site][spot_path_no[spot1]][0].extend([spot1,spot2])
					site_paths[site][spot_path_no[spot1]][0].extend(site_paths[site][spot_path_no[spot2]][0])
					for path in site_paths[site][spot_path_no[spot2]][1:]:
						site_paths[site][spot_path_no[spot1]].append(path)
					spots_tmp=copy.deepcopy(site_paths[site][spot_path_no[spot2]][0])
					site_paths[site][spot_path_no[spot2]]=[]
					for spot3 in spots_tmp:
						spot_path_no[spot3]=spot_path_no[spot1]
					used_spots.extend([spot1,spot2])
			continue
		if (f_orders[f_spot_oid[spot1]][4]+f_orders[f_spot_oid[spot2]][4]>C_load):
			continue
		if (spot1 not in used_spots) and (spot2 not in used_spots):
			spot_path_no[spot1]=spot_path_no[spot2]=now_path_num
			site_paths[site].append([ [spot1,spot2], [spot1,spot2] ])
			now_path_num+=1
			used_spots.extend([spot1,spot2])
			continue
		if (spot1 not in used_spots) and (spot2 in used_spots):
			temp=spot1
			spot1=spot2
			spot2=temp
		if used_spots.count(spot1)==2:
			continue
		now_load=sum([ f_orders[f_spot_oid[val]][4] for val in set(site_paths[site][spot_path_no[spot1]][0]) ])
		if now_load+f_orders[f_spot_oid[spot2]][4]>C_load:
			continue
		site_paths[site][spot_path_no[spot1]][0].extend([spot1,spot2])
		site_paths[site][spot_path_no[spot1]].append([spot1,spot2])
		spot_path_no[spot2]=spot_path_no[spot1]
		used_spots.extend([spot1,spot2])

	for spot in site_spots[site]:
		if spot not in used_spots:
			site_paths[site].append([[spot]])

#网点下路径及消耗
# site_paths= site:*[[所有的边],*[边]] 边=['pointA','pointB']
# site_paths_cost= site:*[[路径],路径总消耗,最后回网点的消耗（可省去）]
for site,paths in site_paths.items():
	site_paths_cost[site]=[]
	for path in paths:
		if path==[]:
			continue
		begin=0
		X=[x for x in path[0] if path[0].count(x)==1]
		if len(X)>2:
			print path
			print X
			print site
		if len(X)==1:
			begin=X[0]
		else:
			begin=X[0] if site_spots_dis[site][X[0]]<site_spots_dis[site][X[1]] else X[1]
		path_cost=[[site,begin],site_spots_dis[site][begin]+serv(f_orders[f_spot_oid[begin]][4])]
		inpath=[]
		for _ in range(len(path)-1):
			for x in path[1:]:
				if x in inpath or begin not in x:
					continue
				begin=x[0] if begin==x[1] else x[1]
				inpath.append(x)
				path_cost[0].append(begin)
				path_cost[1]+=site_spot_spots_dis[site][x[0]][x[1]]+serv(f_orders[f_spot_oid[begin]][4])

		path_cost[0].append(site)
		path_cost[1]+=site_spots_dis[site][begin]
		path_cost.append(site_spots_dis[site][begin])
		site_paths_cost[site].append(path_cost)


site_mans={} #网点下的快递员集合
man_cost={} #快递员耗时
man_paths={} #快递员路径行为
now_dman=1 #当前指向的快递员

#site_mans初始化
for site in site_points:
	site_mans[site]=set()

#网点快递员分配
for _ in range(C_man):
	max_decrement=0 #最大减小量
	best_site=0 #快递员去哪个网点
	best_site_cost=0
	#选出优化度最高的网点
	for site,paths_cost in site_paths_cost.items():
		total_cost=0
		dmans_cost={}
		dmans_lastcost={}
		dman_num=len(site_mans[site])+1 #快递员数量
		for i in range(dman_num):
			dmans_cost[i]=0
			dmans_lastcost[i]=0

		#各快递员耗时计算
		for path_cost in sorted(paths_cost,key=lambda x:x[2]):
			i,useless=sorted(dmans_cost.items(),key=operator.itemgetter(1))[0]

			if dmans_cost[i]>720:#线上订单取货惩罚
				total_cost+=(dmans_cost[i]-720)*C_penalty_tw*(len(path_cost[0])-2)

			for j in range(1,len(path_cost[0])):
				spot1=path_cost[0][j-1]
				spot2=path_cost[0][j]
				dmans_cost[i]+=dist(points[spot1][0],points[spot1][1],points[spot2][0],points[spot2][1])

				if j!=len(path_cost[0])-1:
					if dmans_cost[i]>720:#线上订单送货惩罚
						total_cost+=(dmans_cost[i]-720)*C_penalty_tw
					dmans_cost[i]+=serv(f_orders[f_spot_oid[spot2]][4])

			dmans_lastcost[i]=path_cost[2]

		for i in range(dman_num):
			total_cost+=dmans_cost[i]
			total_cost-=dmans_lastcost[i]
		if site_cost[site]-total_cost>max_decrement:
			max_decrement=site_cost[site]-total_cost
			best_site=site
			best_site_cost=total_cost

	#无法优化
	if max_decrement==0:
		break

	#更新网点快递员、路径、消耗
	site_mans[best_site].add("D%04d" % now_dman)
	now_dman+=1
	man_lastcost={}
	for man in site_mans[best_site]:
		man_cost[man]=0
		man_paths[man]=[]
		man_lastcost[man]=0
	#各快递员耗时计算
	for path_cost in sorted(site_paths_cost[best_site],key=lambda x:x[2]):
		i=0
		for man,useless in sorted(man_cost.items(),key=operator.itemgetter(1)):
			if man in site_mans[best_site]:
				i=man
				break
		man_cost[i]+=path_cost[1]
		man_lastcost[i]=path_cost[2]
		man_paths[i].append(path_cost[0])

	for man in site_mans[best_site]:
		man_cost[man]-=man_lastcost[man]
		man_paths[man][-1]=man_paths[man][-1][:-1]

	site_cost[best_site]=best_site_cost

# ---------------- O2O订单 ----------------------
used_oid=set()
for oid,order in sorted(e_orders.items(),key=lambda x:x[1][2]):
	if oid in used_oid:
		continue
	used_oid.add(oid)
	best_man=0
	bets_cost=0xffffffff
	best_dist=0
	shop_spot=order[1]
	spot=order[0]

	for man,paths in man_paths.items():
		man_spot=paths[-1][-1]#快递员当前所在点
		if man_spot[0]=='E':
			man_spot=e_orders[man_spot][0]
		distance=dist(points[man_spot][0],points[man_spot][1],points[shop_spot][0],points[shop_spot][1])
		tmp=dist(points[shop_spot][0],points[shop_spot][1],points[spot][0],points[spot][1])
		add_cost=distance
		if order[2]>(man_cost[man]+distance):
			add_cost+=(order[2]-man_cost[man]-distance)
		else:
			add_cost+=(man_cost[man]+distance-order[2])*C_penalty_tw*11
		# if (man_cost[man]+distance+tmp) > order[3]:
		# 	add_cost+=(man_cost[man]+distance+tmp-order[3])*C_penalty_tw
		if add_cost<bets_cost:
			bets_cost=add_cost
			best_man=man
			best_dist=distance

	oids=[oid]
	man_cost[best_man]+=best_dist
	man_cost[best_man]=max(order[2],man_cost[best_man])
	man_paths[best_man][-1].append(shop_spot)
	#是否取多个O2O订单,并且假设只取一对[商点，配送点]
	now_oid=oid
	distance=dist(points[spot][0],points[spot][1],points[shop_spot][0],points[shop_spot][1])
	# ----- 调整段 ------
	for next_oid in e_spot_oids[spot]:#相同商点，配送点下，时间应该是升序的
		if (next_oid in used_oid) or (e_orders[next_oid][1]!=shop_spot):
			continue
		#此处判断可设定
		if (man_cost[best_man] >= e_orders[next_oid][2]-8):
			now_oid=next_oid
			used_oid.add(now_oid)
			oids.append(now_oid)
			continue
		#此处判断可设定
		if (e_orders[next_oid][2]-e_orders[now_oid][2]) in [0,1,2,3,10,11,13]:
			now_oid=next_oid
			used_oid.add(now_oid)
			oids.append(now_oid)
			continue

	# ----- 调整段 end------

	path=[shop_spot]
	path.extend(oids)
	man_paths[best_man].append(path)
	man_cost[best_man]=max(man_cost[best_man],e_orders[oids[-1]][2])+distance
	man_cost[best_man]+=sum([ serv(e_orders[x][4]) for x in oids] )

# ----- 生成结果 --------
outFile=open('result.csv','w')
for man,paths in man_paths.items():
	if man_cost[man]==0 or man not in man_paths:
		continue
	ariv=0
	dept=0
	for path in paths:
		begin=path[0]
		if path !=paths[0]:
			ariv+=dist(points[end][0],points[end][1],points[begin][0],points[begin][1])
		end=path[-1] if (path[-1][0]!='A' and path[-1][0]!='S') else path[-2]
		if end[0]=='E':
			end=e_orders[end][0]
		dept=ariv
		for spot in path:
			if spot[0]=='A' or spot[0]=='S':
				continue
			oid=f_spot_oid[spot] if begin[0]=='A' else spot
			num=f_orders[oid][4] if begin[0]=='A' else e_orders[oid][4]
			if begin[0]=='S':
				best_cost=0xffff
				for site in site_points:
					distince=dist(points[site][0],points[site][1],points[begin][0],points[begin][1])
					if distince<best_cost:
						best_cost=distince
				ariv=max(best_cost,ariv)
				dept=max(e_orders[oid][2],ariv)
			outStr="%s,%s,%d,%d,%d,%s\n" \
					 % (man,begin,ariv,dept,num,oid)
			outFile.write(outStr)
			if begin[0]=='S':
				ariv=dept
		for i in range(1,len(path)):
			spot=path[i]
			last_spot=path[i-1]
			if spot[0]=='A' or spot[0]=='S':
				continue
			oid=f_spot_oid[spot] if begin[0]=='A' else spot
			num=f_orders[oid][4] if begin[0]=='A' else e_orders[oid][4]
			if begin[0]=='S':
				spot=e_orders[spot][0]
				if last_spot[0]!='S':
					last_spot=e_orders[last_spot][0]
			ariv+=dist(points[last_spot][0],points[last_spot][1],points[spot][0],points[spot][1])
			dept=ariv+serv(num)
			outStr=outStr="%s,%s,%d,%d,-%d,%s\n" \
					 % (man,spot,ariv,dept,num,oid)
			outFile.write(outStr)
			ariv=dept
