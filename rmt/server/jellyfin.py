import re

import requests
import log
from config import Config
from utils.functions import get_local_time
from utils.types import MediaType


class Jellyfin:
    __apikey = None
    __host = None

    def __init__(self):
        self.init_config()

    # 初始化配置
    def init_config(self):
        config = Config()
        jellyfin = config.get_config('jellyfin')
        if jellyfin:
            self.__host = jellyfin.get('host')
            if not self.__host.startswith('http://') and not self.__host.startswith('https://'):
                self.__host = "http://" + self.__host
            if not self.__host.endswith('/'):
                self.__host = self.__host + "/"
            self.__apikey = jellyfin.get('api_key')

    # 获取Jellyfin媒体库的信息
    def __get_jellyfin_librarys(self):
        if not self.__host or not self.__apikey:
            return []
        req_url = "%sLibrary/MediaFolders?api_key=%s" % (self.__host, self.__apikey)
        try:
            res = requests.get(req_url, timeout=10)
            if res:
                return res.json().get("Items")
            else:
                log.error("【JELLYFIN】Library/MediaFolders 未获取到返回数据")
                return []
        except Exception as e:
            log.error("【JELLYFIN】连接Library/MediaFolders 出错：" + str(e))
            return []

    # 获得用户数量
    def get_user_count(self):
        if not self.__host or not self.__apikey:
            return 0
        req_url = "%sUsers?api_key=%s" % (self.__host, self.__apikey)
        try:
            res = requests.get(req_url, timeout=10)
            if res:
                return len(res.json())
            else:
                log.error("【JELLYFIN】Users 未获取到返回数据")
                return 0
        except Exception as e:
            log.error("【JELLYFIN】连接Users出错：" + str(e))
            return 0

    # 获取Jellyfin活动记录
    def get_activity_log(self, num):
        if not self.__host or not self.__apikey:
            return []
        req_url = "%sSystem/ActivityLog/Entries?api_key=%s&Limit=%s" % (self.__host, self.__apikey, num)
        ret_array = []
        try:
            res = requests.get(req_url, timeout=10)
            if res:
                ret_json = res.json()
                items = ret_json.get('Items')
                for item in items:
                    if item.get("Type") == "SessionStarted":
                        event_type = "LG"
                        event_date = re.sub(r'\.\d{7}Z', '', item.get("Date")).replace("T", " ")
                        event_str = "%s, %s" % (item.get("Name"), item.get("ShortOverview"))
                        activity = {"type": event_type, "event": event_str, "date": event_date}
                        ret_array.append(activity)
                    if item.get("Type") == "VideoPlayback":
                        event_type = "PL"
                        event_date = re.sub(r'\.\d{7}Z', '', item.get("Date")).replace("T", " ")
                        activity = {"type": event_type, "event": item.get("Name"), "date": event_date}
                        ret_array.append(activity)
            else:
                log.error("【JELLYFIN】System/ActivityLog/Entries 未获取到返回数据")
                return []
        except Exception as e:
            log.error("【JELLYFIN】连接System/ActivityLog/Entries出错：" + str(e))
            return []
        return ret_array

    # 获得媒体数量
    def get_medias_count(self):
        if not self.__host or not self.__apikey:
            return None
        req_url = "%sItems/Counts?api_key=%s" % (self.__host, self.__apikey)
        try:
            res = requests.get(req_url, timeout=10)
            if res:
                return res.json()
            else:
                log.error("【JELLYFIN】Items/Counts 未获取到返回数据")
                return {}
        except Exception as e:
            log.error("【JELLYFIN】连接Items/Counts出错：" + str(e))
            return {}

    # 根据名称查询Jellyfin中剧集的SeriesId
    def __get_jellyfin_series_id_by_name(self, name, year):
        if not self.__host or not self.__apikey:
            return None
        req_url = "%sItems?includeItemTypes=Series&fields=ProductionYear&startIndex=0&recursive=true&searchTerm=%s&limit=10&api_key=%s" % (
            self.__host, name, self.__apikey)
        try:
            res = requests.get(req_url, timeout=10)
            if res:
                res_items = res.json().get("Items")
                if res_items:
                    for res_item in res_items:
                        if res_item.get('Name') == name and (
                                not year or str(res_item.get('ProductionYear')) == str(year)):
                            return res_item.get('Id')
        except Exception as e:
            log.error("【JELLYFIN】连接Items出错：" + str(e))
            return None
        return None

    # 根据标题和年份，检查电影是否在Jellyfin中存在，存在则返回列表
    def get_movies(self, title, year=None):
        if not self.__host or not self.__apikey:
            return None
        req_url = "%sItems?includeItemTypes=Movie&fields=ProductionYear&startIndex=0&recursive=true&searchTerm=%s&limit=10&api_key=%s" % (
            self.__host, title, self.__apikey)
        try:
            res = requests.get(req_url, timeout=10)
            if res:
                res_items = res.json().get("Items")
                if res_items:
                    ret_movies = []
                    for res_item in res_items:
                        if res_item.get('Name') == title and (
                                not year or str(res_item.get('ProductionYear')) == str(year)):
                            ret_movies.append(
                                {'title': res_item.get('Name'), 'year': str(res_item.get('ProductionYear'))})
                            return ret_movies
        except Exception as e:
            log.error("【JELLYFIN】连接Items出错：" + str(e))
            return []
        return []

    # 根据标题和年份和季，返回Jellyfin中的剧集列表
    def __get_jellyfin_tv_episodes(self, title, year=None, season=None):
        if not self.__host or not self.__apikey:
            return []
        # 电视剧
        item_id = self.__get_jellyfin_series_id_by_name(title, year)
        if not item_id:
            return []
        # /Shows/{Id}/Episodes 查集的信息
        if not season:
            season = 1
        req_url = "%sShows/%s/Episodes?season=%s&api_key=%s" % (
            self.__host, item_id, season, self.__apikey)
        try:
            res_json = requests.get(req_url, timeout=10)
            if res_json:
                res_items = res_json.json().get("Items")
                exists_episodes = []
                for res_item in res_items:
                    exists_episodes.append(int(res_item.get("IndexNumber")))
                return exists_episodes
        except Exception as e:
            log.error("【JELLYFIN】连接Shows/{Id}/Episodes出错：" + str(e))
            return []

    # 根据标题、年份、季、总集数，查询Jellyfin中缺少哪几集
    def get_no_exists_episodes(self, meta_info, season, total_num):
        if not self.__host or not self.__apikey:
            return None
        exists_episodes = self.__get_jellyfin_tv_episodes(meta_info.title, meta_info.year, season)
        total_episodes = [episode for episode in range(1, total_num + 1)]
        return list(set(total_episodes).difference(set(exists_episodes)))

    # 根据ItemId从Jellyfin查询图片地址
    def get_image_by_id(self, item_id, image_type):
        if not self.__host or not self.__apikey:
            return None
        req_url = "%sItems/%s/RemoteImages?api_key=%s" % (self.__host, item_id, self.__apikey)
        try:
            res = requests.get(req_url, timeout=10)
            if res:
                images = res.json().get("Images")
                for image in images:
                    if image.get("ProviderName") == "TheMovieDb" and image.get("Type") == image_type:
                        return image.get("Url")
            else:
                log.error("【JELLYFIN】Items/RemoteImages 未获取到返回数据")
                return None
        except Exception as e:
            log.error("【JELLYFIN】连接Items/{Id}/RemoteImages出错：" + str(e))
            return None
        return None

    # 通知Jellyfin刷新一个项目的媒体库
    def __refresh_jellyfin_library_by_id(self, item_id):
        if not self.__host or not self.__apikey:
            return False
        req_url = "%sItems/%s/Refresh?Recursive=true&api_key=%s" % (self.__host, item_id, self.__apikey)
        try:
            res = requests.post(req_url, timeout=10)
            if res:
                return True
        except Exception as e:
            log.error("【JELLYFIN】连接Items/{Id}/Refresh出错：" + str(e))
            return False
        return False

    # 通知Jellyfin刷新整个媒体库
    def refresh_root_library(self):
        if not self.__host or not self.__apikey:
            return False
        req_url = "%sLibrary/Refresh?api_key=%s" % (self.__host, self.__apikey)
        try:
            res = requests.post(req_url, timeout=10)
            if res:
                return True
        except Exception as e:
            log.error("【JELLYFIN】连接Library/Refresh出错：" + str(e))
            return False
        return False

    # 按类型、名称、年份来刷新媒体库
    def refresh_library_by_items(self, items):
        if not items:
            return
        # 收集要刷新的媒体库信息
        log.info("【JELLYFIN】开始刷新Jellyfin媒体库...")
        library_ids = []
        for item in items:
            if not item:
                continue
            library_id = self.__get_jellyfin_library_id_by_item(item)
            if library_id and library_id not in library_ids:
                library_ids.append(library_id)
        # 开始刷新媒体库
        if "/" in library_ids:
            self.refresh_root_library()
            return
        for library_id in library_ids:
            if library_id != "/":
                self.__refresh_jellyfin_library_by_id(library_id)
        log.info("【JELLYFIN】Jellyfin媒体库刷新完成")

    # 根据媒体信息查询在哪个媒体库，返回要刷新的位置的ID
    def __get_jellyfin_library_id_by_item(self, item):
        if not item.get("title") or not item.get("year") or not item.get("type"):
            return None
        if item.get("type") == MediaType.TV:
            item_id = self.__get_jellyfin_series_id_by_name(item.get("title"), item.get("year"))
            if item_id:
                # 存在电视剧，则直接刷新这个电视剧就行
                return item_id
        else:
            if self.get_movies(item.get("title"), item.get("year")):
                # 已存在，不用刷新
                return None
        # 查找需要刷新的媒体库ID
        for library in self.__get_jellyfin_librarys():
            for folder in library.get("Path"):
                if "/%s" % item.get("category") in folder.get("Path"):
                    return library.get("Id")
        # 刷新根目录
        return "/"
