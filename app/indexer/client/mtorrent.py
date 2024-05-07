import base64
import json
import re
from datetime import datetime
from typing import Tuple, List

import log
from app.conf.systemconfig_oper import SystemConfigOper
from app.helper import IndexerConf
from app.utils import RequestUtils
from app.utils.string_utils import StringUtils
from app.utils.types import MediaType
from config import Config


class MTorrentSpider:
    """
    mTorrent API，需要缓存ApiKey
    """
    _indexerid = None
    _domain = None
    _name = ""
    _proxy = None
    _cookie = None
    _ua = None
    _size = 100
    _searchurl = "%sapi/torrent/search"
    _downloadurl = "%sapi/torrent/genDlToken"
    _pageurl = "%sdetail/%s"

    # 电影分类
    _movie_category = ['401', '419', '420', '421', '439', '405', '404']
    _tv_category = ['403', '402', '435', '438', '404', '405']

    # API KEY
    _apikey = None
    _token = None

    # 标签
    _labels = {
        "0": "",
        "1": "DIY",
        "2": "国配",
        "3": "DIY 国配",
        "4": "中字",
        "5": "DIY 中字",
        "6": "国配 中字",
        "7": "DIY 国配 中字"
    }

    def __init__(self, indexer: IndexerConf):
        if indexer:
            self._indexerid = indexer.id
            self._domain = indexer.domain
            self._searchurl = self._searchurl % self._domain
            self._name = indexer.name
            self._proxy = None
            self._cookie = indexer.cookie
            self._ua = indexer.ua
            self._apikey = indexer.apikey
            self._token = indexer.token


    def search(self, keyword: str, mtype: MediaType = None, mode: str = None, page: int = 0) -> Tuple[bool, List[dict]]:
        """
        搜索
        """
        # 检查ApiKey
        if not self._apikey:
            return True, []

        if not mtype:
            categories = []
        elif mtype == MediaType.TV:
            categories = self._tv_category
        else:
            categories = self._movie_category
        params = {
            "keyword": keyword,
            "categories": categories,
            "pageNumber": int(page) + 1,
            "pageSize": self._size,
            "visible": 1,
        }
        if mode == 'adult':
            params["mode"] = mode

        res = RequestUtils(
            headers={
                "Content-Type": "application/json",
                "User-Agent": self._ua or f"{Config().get_ua()}",
                "x-api-key": self._apikey
            },
            proxies=self._proxy,
            referer=f"{self._domain}browse",
            timeout=15
        ).post_res(url=self._searchurl, json=params)
        torrents = []
        if res and res.status_code == 200:
            results = res.json().get('data', {}).get("data") or []
            for result in results:
                category_value = result.get('category')
                if category_value in self._tv_category \
                        and category_value not in self._movie_category:
                    category = MediaType.TV.value
                elif category_value in self._movie_category:
                    category = MediaType.MOVIE.value
                else:
                    category = MediaType.UNKNOWN.value
                labels_value = self._labels.get(result.get('labels') or "0") or ""
                if labels_value:
                    labels = labels_value.split()
                else:
                    labels = []
                torrent = {
                    'title': self.__get_title(result.get('name')),
                    'description': result.get('smallDescr'),
                    'enclosure': self.__get_download_url(result.get('id')),
                    'pubdate': self.__get_pub_time(StringUtils.format_timestamp(result.get('createdDate'))),
                    'date_elapsed': self.__get_pub_time(StringUtils.format_timestamp(result.get('createdDate'))),
                    'size': int(result.get('size') or '0'),
                    'seeders': int(result.get('status', {}).get("seeders") or '0'),
                    'peers': int(result.get('status', {}).get("leechers") or '0'),
                    'grabs': int(result.get('status', {}).get("timesCompleted") or '0'),
                    'downloadvolumefactor': self.__get_downloadvolumefactor(result.get('status', {}).get("discount")),
                    'uploadvolumefactor': self.__get_uploadvolumefactor(result.get('status', {}).get("discount")),
                    'endtime': self.__get_end_time(result.get('status', {}).get("discountEndTime")),
                    'page_url': self._pageurl % (self._domain, result.get('id')),
                    'imdbid': self.__find_imdbid(result.get('imdb')),
                    'labels': labels,
                    'category': category
                }
                torrents.append(torrent)
        elif res is not None:
            log.warn(f"{self._name} 搜索失败，错误码：{res.status_code}")
            return True, []
        else:
            log.warn(f"{self._name} 搜索失败，无法连接 {self._domain}")
            return True, []
        return False, torrents

    @staticmethod
    def __get_title(name: str) -> str:
        if not name:
            return name
        if len(name) < 50:
            return name
        return name[:50] + "..."

    @staticmethod
    def __find_imdbid(imdb: str) -> str:
        """
        从imdb链接中提取imdbid
        """
        if imdb:
            m = re.search(r"tt\d+", imdb)
            if m:
                return m.group(0)
        return ""

    @staticmethod
    def __get_downloadvolumefactor(discount: str) -> float:
        """
        获取下载系数
        """
        discount_dict = {
            "FREE": 0,
            "PERCENT_50": 0.5,
            "PERCENT_70": 0.3,
            "_2X_FREE": 0,
            "_2X_PERCENT_50": 0.5
        }
        if discount:
            return discount_dict.get(discount, 1)
        return 1

    @staticmethod
    def __get_uploadvolumefactor(discount: str) -> float:
        """
        获取上传系数
        """
        uploadvolumefactor_dict = {
            "_2X": 2.0,
            "_2X_FREE": 2.0,
            "_2X_PERCENT_50": 2.0
        }
        if discount:
            return uploadvolumefactor_dict.get(discount, 1)
        return 1

    def __get_download_url(self, torrent_id: str) -> str:
        """
        获取下载链接，返回base64编码的json字符串及URL
        """
        url = self._downloadurl % self._domain
        params = {
            'method': 'post',
            'cookie': False,
            'params': {
                'id': torrent_id
            },
            'header': {
                'Content-Type': 'application/json',
                'User-Agent': f'{self._ua}',
                'Accept': 'application/json, text/plain, */*',
                'x-api-key': self._apikey
            },
            'result': 'data'
        }
        # base64编码
        base64_str = base64.b64encode(json.dumps(params).encode('utf-8')).decode('utf-8')
        return f"[{base64_str}]{url}"

    def __get_pub_time(self, given_time_str: None):
        if not given_time_str:
            return ''
        given_time = datetime.strptime(given_time_str, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        time_difference = now - given_time
        if time_difference.days > 0:
            return f"{time_difference.days}天"
        # 如果时间差不足一天，则计算小时数
        elif (time_difference.seconds // 3600) > 0:
            return f"{time_difference.seconds // 3600}小时"
        else:
            return f"{time_difference.seconds // 60}分钟"


    def __get_end_time(self, given_time_str: None):
        if not given_time_str:
            return ''
        given_time = datetime.strptime(given_time_str, '%Y-%m-%d %H:%M:%S')
        # 获取当前时间
        now = datetime.now()
        # 计算时间差
        time_difference = given_time - now
        # 如果时间差大于一天，则计算天数
        if time_difference.days > 0:
           return f"限时：{time_difference.days} 天 {time_difference.seconds // 3600} 小时内"
        # 如果时间差不足一天，则计算小时数
        elif (time_difference.seconds // 3600) > 0:
            return f"限时：{time_difference.seconds // 3600} 小时内"
        else:
            return f"限时：{time_difference.seconds // 60} 分钟内"
