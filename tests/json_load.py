import json
import pickle

# 加载数据
with open(r'/Users/jiayun/soft/github-projects/fullnastools/config/sites.dat', 'rb') as f:
    data = pickle.load(f)
print(json.dumps(data, indent=4))
# 对数据进行修改
for d in data :
   if d['id'] == 'mteamss' :
       print(d)
       d['domain'] ='https://xp.m-team.io/'
       d['parser'] ='mTorrent'
       d['ext_domains'] = [
           "https://xp.m-team.cc/",
           "https://kp.m-team.cc/"
       ]
   elif d['id']== 'pttime':
       d['search']['paths'] = [
           {
               "path": "torrents.php",
               "type": "all",
               "method": "get"
           },
           {
               "path": "adults.php",
               "type": "adult",
               "method": "get"
           }
       ]

       print(d)

# 将修改后的数据写回文件
#with open(r'/Users/jiayun/soft/github-projects/fullnastools/config/sites.dat', 'wb') as f:
 #   pickle.dump(data, f)
   # pass


