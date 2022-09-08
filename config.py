import os
import shutil
from threading import Lock

import ruamel.yaml
from werkzeug.security import generate_password_hash

from app.utils.commons import singleton

# 菜单对应关系，配置WeChat应用中配置的菜单ID与执行命令的对应关系，需要手工修改
# 菜单序号在https://work.weixin.qq.com/wework_admin/frame#apps 应用自定义菜单中维护，然后看日志输出的菜单序号是啥（按顺利能猜到的）....
# 命令对应关系：/ptt 下载文件转移；/ptr 删种；/pts 站点签到；/rst 目录同步；/rss RSS下载
from app.utils.string_utils import StringUtils

WECHAT_MENU = {'_0_0': '/ptt', '_0_1': '/ptr', '_0_2': '/rss', '_1_0': '/rst', '_1_1': '/db', '_2_0': '/pts'}
# 收藏了的媒体的目录名，名字可以改，在Emby中点击红星则会自动将电影转移到此分类下，需要在Emby Webhook中配置用户行为通知
RMT_FAVTYPE = '精选'
# 支持的媒体文件后缀格式
RMT_MEDIAEXT = ['.mp4', '.mkv', '.ts', '.iso', '.rmvb', '.avi', '.mov', '.mpeg', '.mpg', '.wmv', '.3gp', '.asf', '.m4v',
                '.flv', '.m2ts']
# 支持的字幕文件后缀格式
RMT_SUBEXT = ['.srt', '.ass', '.ssa']
# 电视剧动漫的分类genre_ids
ANIME_GENREIDS = ['16']
# 默认过滤的文件大小，150M
RMT_MIN_FILESIZE = 150 * 1024 * 1024
# 删种检查时间间隔
AUTO_REMOVE_TORRENTS_INTERVAL = 1800
# 下载文件转移检查时间间隔，
PT_TRANSFER_INTERVAL = 300
# TMDB信息缓存定时保存时间
METAINFO_SAVE_INTERVAL = 600
# 配置文件定时生效时间
RELOAD_CONFIG_INTERVAL = 600
# SYNC目录同步聚合转移时间
SYNC_TRANSFER_INTERVAL = 60
# RSS队列中处理时间间隔
RSS_CHECK_INTERVAL = 300
# 站点流量数据刷新时间间隔（小时）
REFRESH_PT_DATA_INTERVAL = 6
# 刷新订阅TMDB数据的时间间隔（小时）
RSS_REFRESH_TMDB_INTERVAL = 6
# 刷流删除的检查时间间隔
BRUSH_REMOVE_TORRENTS_INTERVAL = 600
# 定时清除未识别的缓存时间间隔（小时）
META_DELETE_UNKNOWN_INTERVAL = 12
# 定时刷新壁纸的间隔（小时）
REFRESH_WALLPAPER_INTERVAL = 1
# fanart的api，用于拉取封面图片
FANART_MOVIE_API_URL = 'https://webservice.fanart.tv/v3/movies/%s?api_key=d2d31f9ecabea050fc7d68aa3146015f'
FANART_TV_API_URL = 'https://webservice.fanart.tv/v3/tv/%s?api_key=d2d31f9ecabea050fc7d68aa3146015f'
# 默认背景图地址
DEFAULT_TMDB_IMAGE = 'https://s3.bmp.ovh/imgs/2022/07/10/77ef9500c851935b.webp'
# 默认微信消息代理服务器地址
DEFAULT_WECHAT_PROXY = 'https://nastool.jxxghp.cn'
# TMDB图片地址
TMDB_IMAGE_W500_URL = 'https://image.tmdb.org/t/p/w500%s'
TMDB_IMAGE_ORIGINAL_URL = 'https://image.tmdb.org/t/p/original/%s'
# 添加下载时增加的标签，开始只监控NASTool添加的下载时有效
PT_TAG = "NASTOOL"
# 搜索种子过滤属性
TORRENT_SEARCH_PARAMS = {
    "restype": {
        "BLURAY": r"Blu-?Ray|BD|BDRIP",
        "REMUX": r"REMUX",
        "DOLBY": r"DOLBY",
        "WEB": r"WEB-?DL|WEBRIP",
        "HDTV": r"U?HDTV",
        "UHD": r"UHD",
        "HDR": r"HDR",
        "3D": r"3D"
    },
    "pix": {
        "8k": r"8K",
        "4k": r"4K|2160P|X2160",
        "1080p": r"1080[PIX]|X1080",
        "720p": r"720P"
    }
}
# 电影默认命名格式
DEFAULT_MOVIE_FORMAT = '{title} ({year})/{title} ({year})-{part} - {videoFormat}'
# 电视剧默认命名格式
DEFAULT_TV_FORMAT = '{title} ({year})/Season {season}/{title} - {season_episode}-{part} - 第 {episode} 集'

lock = Lock()


@singleton
class Config(object):
    __config = {}
    __config_path = None

    def __init__(self):
        self.__config_path = os.environ.get('NASTOOL_CONFIG')
        self.init_config()

    def init_config(self):
        try:
            if not self.__config_path:
                print("【ERROR】NASTOOL_CONFIG 环境变量未设置，程序无法工作，正在退出...")
                quit()
            if not os.path.exists(self.__config_path):
                cfg_tp_path = os.path.join(self.get_inner_config_path(), "config.yaml")
                cfg_tp_path = cfg_tp_path.replace("\\", "/")
                shutil.copy(cfg_tp_path, self.__config_path)
                print("【ERROR】config.yaml 配置文件不存在，已将配置文件模板复制到配置目录...")
            with open(self.__config_path, mode='r', encoding='utf-8') as f:
                try:
                    # 读取配置
                    self.__config = ruamel.yaml.YAML().load(f)
                    overwrite_cofig = False
                    # 密码初始化
                    login_password = self.__config.get("app", {}).get("login_password")
                    if login_password and not login_password.startswith("[hash]"):
                        self.__config['app']['login_password'] = "[hash]%s" % generate_password_hash(login_password)
                        overwrite_cofig = True
                    # 实验室配置初始化
                    if not self.__config.get("laboratory"):
                        self.__config['laboratory'] = {}
                        overwrite_cofig = True
                    # 安全配置初始化
                    if not self.__config.get("security"):
                        self.__config['security'] = {
                            'media_server_webhook_allow_ip': {
                                'ipv4': '0.0.0.0/0',
                                'ipv6': '::/0'
                            },
                            'telegram_webhook_allow_ip': {
                                'ipv4': '149.154.160.0/20,91.108.4.0/22',
                                'ipv6': '::/0'
                            }
                        }
                        overwrite_cofig = True
                    # API密钥初始化
                    if not self.__config.get("security", {}).get("subscribe_token"):
                        self.__config['security']['subscribe_token'] = self.__config.get("laboratory",
                                                                                         {}).get("subscribe_token") \
                                                                       or StringUtils.generate_random_str()
                        overwrite_cofig = True
                    # 消息推送开关初始化
                    if not self.__config.get("message", {}).get("switch"):
                        self.__config['message']['switch'] = {
                            "download_start": True,
                            "download_fail": True,
                            "transfer_finished": True,
                            "transfer_fail": True,
                            "rss_added": True,
                            "rss_finished": True,
                            "site_signin": True
                        }
                        overwrite_cofig = True
                    # 刮削配置初始化
                    if self.__config.get("media", {}).get("nfo_poster"):
                        if not self.__config.get("scraper_nfo"):
                            self.__config['scraper_nfo'] = {
                                "movie": {
                                    "basic": True,
                                    "credits": True,
                                    "credits_chinese": True},
                                "tv": {
                                    "basic": True,
                                    "credits": True,
                                    "credits_chinese": True,
                                    "season_basic": True,
                                    "episode_basic": True,
                                    "episode_credits": True}
                            }
                            overwrite_cofig = True
                        if not self.__config.get("scraper_pic"):
                            self.__config['scraper_pic'] = {
                                "movie": {
                                    "poster": True,
                                    "backdrop": True,
                                    "background": True,
                                    "logo": True,
                                    "disc": True,
                                    "banner": True,
                                    "thumb": True},
                                "tv": {
                                    "poster": True,
                                    "backdrop": True,
                                    "background": True,
                                    "logo": True,
                                    "clearart": True,
                                    "banner": True,
                                    "thumb": True,
                                    "season_poster": True,
                                    "season_banner": True,
                                    "season_thumb": True}
                            }
                            overwrite_cofig = True
                    # 重写配置文件
                    if overwrite_cofig:
                        self.save_config(self.__config)
                except Exception as e:
                    print("【ERROR】配置文件 config.yaml 格式出现严重错误！请检查：%s" % str(e))
                    self.__config = {}
        except Exception as err:
            print("【ERROR】加载 config.yaml 配置出错：%s" % str(err))
            return False

    def get_proxies(self):
        return self.get_config('app').get("proxies")

    def get_config(self, node=None):
        if not node:
            return self.__config
        return self.__config.get(node, {})

    def save_config(self, new_cfg):
        self.__config = new_cfg
        with open(self.__config_path, mode='w', encoding='utf-8') as f:
            yaml = ruamel.yaml.YAML()
            return yaml.dump(new_cfg, f)

    def get_config_path(self):
        return os.path.dirname(self.__config_path)

    @staticmethod
    def get_root_path():
        return os.path.dirname(os.path.realpath(__file__))

    def get_inner_config_path(self):
        return os.path.join(self.get_root_path(), "config")
