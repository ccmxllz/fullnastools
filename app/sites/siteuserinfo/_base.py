# -*- coding: utf-8 -*-
import base64
import json
import re
from abc import ABCMeta, abstractmethod
from urllib.parse import urljoin, urlsplit

import requests
from lxml import etree

import log
from app.helper import SiteHelper
from app.utils import RequestUtils
from app.utils.types import SiteSchema

SITE_BASE_ORDER = 1000


class _ISiteUserInfo(metaclass=ABCMeta):
    # 站点模版
    schema = SiteSchema.NexusPhp
    # 站点解析时判断顺序，值越小越先解析
    order = SITE_BASE_ORDER

    # 请求模式 cookie/apikey
    request_mode = "cookie"

    def __init__(self, site_name, url, site_cookie, index_html, session=None, ua=None, apikey=None, token=None):
        super().__init__()
        # 站点信息
        self.site_name = None
        self.site_url = None
        self.site_favicon = None
        self.apikey = apikey
        self.token = token
        # 用户信息
        self.username = None
        self.userid = None


        # 未读消息
        self.message_unread = 0
        self.message_unread_contents = []

        # 流量信息
        self.upload = 0
        self.download = 0
        self.ratio = 0

        # 种子信息
        self.seeding = 0
        self.leeching = 0
        self.uploaded = 0
        self.completed = 0
        self.incomplete = 0
        self.seeding_size = 0
        self.leeching_size = 0
        self.uploaded_size = 0
        self.completed_size = 0
        self.incomplete_size = 0
        # 做种人数, 种子大小
        self.seeding_info = []

        # 用户详细信息
        self._user_basic_page = None
        self._user_basic_params = None
        self._user_basic_headers = None
        self.user_level = None
        self.join_at = None
        self.bonus = 0.0

        # 错误信息
        self.err_msg = None
        # 内部数据
        self._base_url = None
        self._site_cookie = None
        self._index_html = None
        self._addition_headers = None

        # 站点页面
        self._brief_page = "index.php"
        self._user_detail_page = "userdetails.php?id="
        self._user_traffic_page = "index.php"
        self._torrent_seeding_page = "getusertorrentlistajax.php?userid="
        self._user_mail_unread_page = "messages.php?action=viewmailbox&box=1&unread=yes"
        self._sys_mail_unread_page = "messages.php?action=viewmailbox&box=-2&unread=yes"
        self._torrent_seeding_params = None
        self._torrent_seeding_headers = None
        self._user_detail_params = None
        self._user_detail_headers = None

        split_url = urlsplit(url)
        self.site_name = site_name
        self.site_url = url
        self._base_url = f"{split_url.scheme}://{split_url.netloc}"
        self._favicon_url = urljoin(self._base_url, "favicon.ico")
        self.site_favicon = ""
        self._site_cookie = site_cookie
        self._index_html = index_html
        self._session = session if session else requests.Session()
        self._ua = ua

    def site_schema(self):
        """
        站点解析模型
        :return: 站点解析模型
        """
        return self.schema

    @classmethod
    def match(cls, html_text):
        """
        是否匹配当前解析模型
        :param html_text: 站点首页html
        :return: 是否匹配
        """
        return False

    def parse(self):
        """
        解析站点信息
        :return:
        """
        self._parse_favicon(self._index_html)
        if not self._parse_logged_in(self._index_html):
            return

        self._parse_site_page(self._index_html)

        # 解析用户基础信息
        if self._user_basic_page:
            self._parse_user_base_info(
                self._get_page_content(
                    url=urljoin(self._base_url, self._user_basic_page),
                    params=self._user_basic_params,
                    headers=self._user_basic_headers
                )
            )
        else:
            self._parse_user_base_info(self._index_html)
        # 解析用户详细信息
        if self._user_detail_page:
            self._parse_user_detail_info(
                self._get_page_content(
                    url=urljoin(self._base_url, self._user_detail_page),
                    params=self._user_detail_params,
                    headers=self._user_detail_headers
                )
            )
        # 解析用户未读消息
        self._pase_unread_msgs()
        # 解析用户上传、下载、分享率等信息
        if self._user_traffic_page:
            self._parse_user_traffic_info(
                self._get_page_content(
                    url=urljoin(self._base_url, self._user_traffic_page),
                    params=self._user_traffic_params,
                    headers=self._user_traffic_headers
                )
            )
        # 解析用户做种信息
        self._parse_seeding_pages()
        self.seeding_info = json.dumps(self.seeding_info)

    def _pase_unread_msgs(self):
        """
        解析所有未读消息标题和内容
        :return:
        """
        unread_msg_links = []
        if self.message_unread > 0:
            links = {self._user_mail_unread_page, self._sys_mail_unread_page}
            for link in links:
                if not link:
                    continue

                msg_links = []
                next_page = self._parse_message_unread_links(
                    self._get_page_content(urljoin(self._base_url, link)), msg_links)
                while next_page:
                    next_page = self._parse_message_unread_links(
                        self._get_page_content(urljoin(self._base_url, next_page)), msg_links)

                unread_msg_links.extend(msg_links)

        for msg_link in unread_msg_links:
            print(msg_link)
            log.debug(f"【Sites】{self.site_name} 信息链接 {msg_link}")
            head, date, content = self._parse_message_content(self._get_page_content(urljoin(self._base_url, msg_link)))
            log.debug(f"【Sites】{self.site_name} 标题 {head} 时间 {date} 内容 {content}")
            self.message_unread_contents.append((head, date, content))

    def _parse_seeding_pages(self):
        seeding_pages = []
        if self._torrent_seeding_page:
            if isinstance(self._torrent_seeding_page, list):
                seeding_pages.extend(self._torrent_seeding_page)
            else:
                seeding_pages.append(self._torrent_seeding_page)

            for seeding_page in seeding_pages:
                # 第一页
                next_page = self._parse_user_torrent_seeding_info(
                    self._get_page_content(urljoin(self._base_url, seeding_page),
                                           self._torrent_seeding_params,
                                           self._torrent_seeding_headers))

                # 其他页处理
                while next_page:
                    next_page = self._parse_user_torrent_seeding_info(
                        self._get_page_content(urljoin(urljoin(self._base_url, seeding_page), next_page),
                                               self._torrent_seeding_params,
                                               self._torrent_seeding_headers),
                        multi_page=True)

    @staticmethod
    def _prepare_html_text(html_text):
        """
        处理掉HTML中的干扰部分
        """
        return re.sub(r"#\d+", "", re.sub(r"\d+px", "", html_text))

    @abstractmethod
    def _parse_message_unread_links(self, html_text, msg_links):
        """
        获取未阅读消息链接
        :param html_text:
        :return:
        """
        pass

    def _parse_favicon(self, html_text):
        """
        解析站点favicon,返回base64 fav图标
        :param html_text:
        :return:
        """
        html = etree.HTML(html_text)
        if html:
            fav_link = html.xpath('//head/link[contains(@rel, "icon")]/@href')
            if fav_link:
                self._favicon_url = urljoin(self._base_url, fav_link[0])

        res = RequestUtils(cookies=self._site_cookie, session=self._session, timeout=60, headers=self._ua).get_res(
            url=self._favicon_url)
        if res:
            self.site_favicon = base64.b64encode(res.content).decode()

    def _get_page_content(self, url, params=None, headers=None):
        """
        :param url: 网页地址
        :param params: post参数
        :param headers: 额外的请求头
        :return:
        """
        req_headers = None
        if self._ua or headers or self._addition_headers:
            req_headers = {
                "User-Agent": f"{self._ua}"
            }
            if headers:
                req_headers.update(headers)

            if  isinstance(self._ua, str):
                req_headers.update({
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "User-Agent": f"{self._ua}"
                })
            else:
                req_headers.update(self._ua)

            if self._addition_headers:
                req_headers.update(self._addition_headers)

        if self.request_mode == "apikey":
            # 使用apikey请求，通过请求头传递
            cookie = None
            session = None
        else:
            # 使用cookie请求
            cookie = self._site_cookie
            session = self._session

        if params:
            res = RequestUtils(cookies=cookie, session=session, timeout=60,
                               headers=req_headers).post_res(
                url=url, params=params)
        else:
            res = RequestUtils(cookies=cookie, session=session, timeout=60,
                               headers=req_headers).get_res(
                url=url)
        if res is not None and res.status_code in (200, 500):
            if "charset=utf-8" in res.text or "charset=UTF-8" in res.text:
                res.encoding = "UTF-8"
            else:
                res.encoding = res.apparent_encoding
            return res.text

        return ""

    @abstractmethod
    def _parse_site_page(self, html_text):
        """
        解析站点相关信息页面
        :param html_text:
        :return:
        """
        pass

    @abstractmethod
    def _parse_user_base_info(self, html_text):
        """
        解析用户基础信息
        :param html_text:
        :return:
        """
        pass

    def _parse_logged_in(self, html_text):
        """
        解析用户是否已经登陆
        :param html_text:
        :return: True/False
        """
        logged_in = SiteHelper.is_logged_in(html_text)
        if not logged_in:
            self.err_msg = "未检测到已登陆，请检查cookies是否过期"
            log.warn(f"【Sites】{self.site_name} 未登录，跳过后续操作")

        return logged_in

    @abstractmethod
    def _parse_user_traffic_info(self, html_text):
        """
        解析用户的上传，下载，分享率等信息
        :param html_text:
        :return:
        """
        pass

    @abstractmethod
    def _parse_user_torrent_seeding_info(self, html_text, multi_page=False):
        """
        解析用户的做种相关信息
        :param html_text:
        :param multi_page: 是否多页数据
        :return: 下页地址
        """
        pass

    @abstractmethod
    def _parse_user_detail_info(self, html_text):
        """
        解析用户的详细信息
        加入时间/等级/魔力值等
        :param html_text:
        :return:
        """
        pass

    @abstractmethod
    def _parse_message_content(self, html_text):
        """
        解析短消息内容
        :param html_text:
        :return:  head: message, date: time, content: message content
        """
        pass
