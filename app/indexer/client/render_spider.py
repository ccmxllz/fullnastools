import copy
import time
from urllib.parse import quote

from pyquery import PyQuery
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as es
from selenium.webdriver.support.wait import WebDriverWait

from app.helper import ChromeHelper
from app.indexer.client.spider import TorrentSpider
from app.utils import ExceptionUtils
from config import Config


class RenderSpider(object):

    torrentspider = None
    torrents_info_array = []
    result_num = 100

    def __init__(self):
        self.torrentspider = TorrentSpider()
        self.init_config()

    def init_config(self):
        self.torrents_info_array = []
        self.result_num = Config().get_config('pt').get('site_search_result_num') or 100

    def search(self, keyword, indexer, page=None):
        if not indexer:
            return []
        if not keyword:
            keyword = ""
        chrome = ChromeHelper()
        if not chrome.get_status():
            return []
        # ����·��
        torrentspath = indexer.search.get('paths', [{}])[0].get('path', '') or ''
        search_url = indexer.domain + torrentspath.replace("{keyword}", quote(keyword))
        # ����ʽ��֧��GET���������
        method = indexer.search.get('paths', [{}])[0].get('method', '')
        if method == "chrome":
            # �������
            params = indexer.search.get('paths', [{}])[0].get('params', {})
            # ������
            search_input = params.get('keyword')
            # ������ť
            search_button = params.get('submit')
            # Ԥִ�нű�
            pre_script = params.get('script')
            # referer
            if params.get('referer'):
                referer = indexer.domain + params.get('referer').replace('{keyword}', quote(keyword))
            else:
                referer = indexer.domain
            if not search_input or not search_button:
                return []
            # ʹ���������ҳ��
            if not chrome.visit(url=search_url,
                                cookie=indexer.cookie,
                                ua=indexer.ua):
                return []
            cloudflare = chrome.pass_cloudflare()
            if not cloudflare:
                return []
            # ģ����������
            try:
                # ִ�нű�
                if pre_script:
                    chrome.execute_script(pre_script)
                # �ȴ��ɵ��
                submit_obj = WebDriverWait(driver=chrome.browser,
                                           timeout=10).until(es.element_to_be_clickable((By.XPATH,
                                                                                        search_button)))
                if submit_obj:
                    # �����û���
                    chrome.browser.find_element(By.XPATH, search_input).send_keys(keyword)
                    # �ύ����
                    submit_obj.click()
                else:
                    return []
            except Exception as e:
                ExceptionUtils.exception_traceback(e)
                return []
        else:
            # referer
            referer = indexer.domain
            # ʹ���������ȡHTML�ı�
            if not chrome.visit(url=search_url,
                                cookie=indexer.cookie,
                                ua=indexer.ua):
                return []
            cloudflare = chrome.pass_cloudflare()
            if not cloudflare:
                return []
        # �ȴ�ҳ��������
        time.sleep(10)
        # ��ȡHTML�ı�
        html_text = chrome.get_html()
        if not html_text:
            return []
        # ���»�ȡCookie��UA
        indexer.cookie = chrome.get_cookies()
        indexer.ua = chrome.get_ua()
        # ����ץ�����
        self.torrentspider.setparam(keyword=keyword,
                                    indexer=indexer,
                                    referer=referer,
                                    page=page)
        # ����ɸѡ��
        torrents_selector = indexer.torrents.get('list', {}).get('selector', '')
        if not torrents_selector:
            return []
        # ����HTML�ı�
        html_doc = PyQuery(html_text)
        for torn in html_doc(torrents_selector):
            self.torrents_info_array.append(copy.deepcopy(self.torrentspider.Getinfo(PyQuery(torn))))
            if len(self.torrents_info_array) >= int(self.result_num):
                break
        return self.torrents_info_array
