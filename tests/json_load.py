import pickle

# 加载数据
with open(r'D:\GitRepo\github_other\fullnastools\config\sites.dat', 'rb') as f:
    data = pickle.load(f)

# 对数据进行修改
for d in data :
   if d['id'] == 'mteam' :
       print(d)
       d['domain'] ='https://xp.m-team.io/'
       d['parser'] ='mTorrent'
       d['ext_domains'] = [
           "https://xp.m-team.cc/",
           "https://kp.m-team.cc/"
       ]
       print(d)

# 将修改后的数据写回文件
#with open(r'D:\GitRepo\github_other\fullnastools\config\sites.dat', 'wb') as f:
 #   pickle.dump(data, f)
   # pass


