from flask import Blueprint, request
from flask_restx import Api, reqparse, Resource

from app.mediaserver import MediaServer
from app.sites import Sites
from app.utils import TokenCache
from config import Config
from web.action import WebAction
from web.backend.user import User
from web.security import require_auth, login_required, generate_access_token

apiv1_bp = Blueprint("apiv1",
                     __name__,
                     static_url_path='',
                     static_folder='./frontend/static/',
                     template_folder='./frontend/', )
Apiv1 = Api(apiv1_bp,
            version="1.0",
            title="NAStool Api",
            description="",
            doc="/",
            security='Bearer Auth',
            authorizations={"Bearer Auth": {"type": "apiKey", "name": "Authorization", "in": "header"}},
            )
# API分组
user = Apiv1.namespace('user', description='用户')
system = Apiv1.namespace('system', description='系统')
config = Apiv1.namespace('config', description='设置')
site = Apiv1.namespace('site', description='站点')
service = Apiv1.namespace('service', description='服务')
subscribe = Apiv1.namespace('subscribe', description='订阅')
rss = Apiv1.namespace('rss', description='自定义RSS')
recommend = Apiv1.namespace('recommend', description='推荐')
search = Apiv1.namespace('search', description='搜索')
download = Apiv1.namespace('download', description='下载')
organization = Apiv1.namespace('organization', description='整理')
library = Apiv1.namespace('library', description='媒体库')
brushtask = Apiv1.namespace('brushtask', description='刷流')
media = Apiv1.namespace('media', description='媒体')
sync = Apiv1.namespace('sync', description='目录同步')
filterrule = Apiv1.namespace('filterrule', description='过滤规则')
words = Apiv1.namespace('words', description='识别词')


class ApiResource(Resource):
    """
    API 认证
    """
    method_decorators = [require_auth]


class ClientResource(Resource):
    """
    登录认证
    """
    method_decorators = [login_required]


def Failed():
    """
    返回失败报名
    """
    return {
        "code": -1,
        "success": False,
        "data": {}
    }


@user.route('/login')
class UserLogin(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username', type=str, help='用户名', location='form', required=True)
    parser.add_argument('password', type=str, help='密码', location='form', required=True)

    @user.doc(parser=parser)
    def post(self):
        """
        用户登录
        """
        args = self.parser.parse_args()
        username = args.get('username')
        password = args.get('password')
        if not username or not password:
            return {"code": 1, "success": False, "message": "用户名或密码错误"}
        user_info = User().get_user(username)
        if not user_info:
            return {"code": 1, "success": False, "message": "用户名或密码错误"}
        # 校验密码
        if not user_info.verify_password(password):
            return {"code": 1, "success": False, "message": "用户名或密码错误"}
        # 缓存Token
        token = generate_access_token(username)
        TokenCache.set(token, token)
        return {
            "code": 0,
            "success": True,
            "data": {
                "token": token,
                "apikey": Config().get_config("security").get("api_key"),
                "userinfo": {
                    "userid": user_info.id,
                    "username": user_info.username,
                    "userpris": str(user_info.pris).split(",")
                }
            }
        }


@user.route('/info')
class UserInfo(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('username', type=str, help='用户名', location='form', required=True)

    @user.doc(parser=parser)
    def post(self):
        """
        获取用户信息
        """
        args = self.parser.parse_args()
        username = args.get('username')
        user_info = User().get_user(username)
        if not user_info:
            return {"code": 1, "success": False, "message": "用户名不正确"}
        return {
            "code": 0,
            "success": True,
            "data": {
                "userid": user_info.id,
                "username": user_info.username,
                "userpris": str(user_info.pris).split(",")
            }
        }


@user.route('/manage')
class UserManage(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('oper', type=str, help='操作类型（add 新增/del删除）', location='form', required=True)
    parser.add_argument('name', type=str, help='用户名', location='form', required=True)
    parser.add_argument('pris', type=str, help='权限', location='form')

    @user.doc(parser=parser)
    def post(self):
        """
        用户管理
        """
        return WebAction().api_action(cmd='user_manager', data=self.parser.parse_args())


@service.route('/mediainfo')
class ServiceMediaInfo(ApiResource):
    parser = reqparse.RequestParser()
    parser.add_argument('name', type=str, help='名称', location='args', required=True)

    @service.doc(parser=parser)
    def get(self):
        """
        识别媒体信息（密钥认证）
        """
        return WebAction().api_action(cmd='name_test', data=self.parser.parse_args())


@service.route('/name/test')
class ServiceNameTest(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('name', type=str, help='名称', location='form', required=True)

    @service.doc(parser=parser)
    def post(self):
        """
        名称识别测试
        """
        return WebAction().api_action(cmd='name_test', data=self.parser.parse_args())


@service.route('/rule/test')
class ServiceRuleTest(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('title', type=str, help='名称', location='form', required=True)
    parser.add_argument('subtitle', type=str, help='描述', location='form')
    parser.add_argument('size', type=float, help='大小（GB）', location='form')

    @service.doc(parser=parser)
    def post(self):
        """
        过滤规则测试
        """
        return WebAction().api_action(cmd='rule_test', data=self.parser.parse_args())


@service.route('/network/test')
class ServiceNetworkTest(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('url', type=str, help='URL地址', location='form', required=True)

    @service.doc(parser=parser)
    def post(self):
        """
        网络连接性测试
        """
        return WebAction().api_action(cmd='net_test', data=self.parser.parse_args().get("url"))


@service.route('/run')
class ServiceRun(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('item', type=str, help='服务ID', location='form', required=True)

    @service.doc(parser=parser)
    def post(self):
        """
        运行服务
        """
        return WebAction().api_action(cmd='sch', data=self.parser.parse_args())


@site.route('/statistics')
class SiteStatistic(ApiResource):
    @staticmethod
    def get():
        """
        获取站点数据明细（密钥认证）
        """
        # 返回站点信息
        return {
            "code": 0,
            "success": True,
            "data": {
                "user_statistics": Sites().get_site_user_statistics(encoding="DICT")
            }
        }


@site.route('/sites')
class SiteSites(ApiResource):
    @staticmethod
    def get():
        """
        获取所有站点配置（密钥认证）
        """
        return {
            "code": 0,
            "success": True,
            "data": {
                "user_sites": Sites().get_sites()
            }
        }


@site.route('/update')
class SiteUpdate(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('site_name', type=str, help='站点名称', location='form', required=True)
    parser.add_argument('site_id', type=int, help='更新站点ID', location='form')
    parser.add_argument('site_pri', type=str, help='优先级', location='form')
    parser.add_argument('site_rssurl', type=str, help='RSS地址', location='form')
    parser.add_argument('site_signurl', type=str, help='站点地址', location='form')
    parser.add_argument('site_cookie', type=str, help='Cookie', location='form')
    parser.add_argument('site_note', type=str, help='站点属性', location='form')
    parser.add_argument('site_include', type=str, help='站点用途', location='form')

    @site.doc(parser=parser)
    def post(self):
        """
        新增/删除站点
        """
        return WebAction().api_action(cmd='update_site', data=self.parser.parse_args())


@site.route('/info')
class SiteInfo(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='站点ID', location='form', required=True)

    @site.doc(parser=parser)
    def post(self):
        """
        查询单个站点详情
        """
        return WebAction().api_action(cmd='get_site', data=self.parser.parse_args())


@site.route('/delete')
class SiteDelete(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='站点ID', location='form', required=True)

    @site.doc(parser=parser)
    def post(self):
        """
        删除站点
        """
        return WebAction().api_action(cmd='del_site', data=self.parser.parse_args())


@site.route('/statistics/activity')
class SiteStatisticsActivity(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('name', type=str, help='站点名称', location='form', required=True)

    @site.doc(parser=parser)
    def post(self):
        """
        查询站点 上传/下载/做种数据
        """
        return WebAction().api_action(cmd='get_site_activity', data=self.parser.parse_args())


@site.route('/check')
class SiteCheck(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('url', type=str, help='站点地址', location='form', required=True)

    @site.doc(parser=parser)
    def post(self):
        """
        检查站点是否支持FREE/HR检测
        """
        return WebAction().api_action(cmd='check_site_attr', data=self.parser.parse_args())


@site.route('/statistics/history')
class SiteStatisticsHistory(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('days', type=int, help='时间范围（天）', location='form', required=True)

    @site.doc(parser=parser)
    def post(self):
        """
        查询所有站点历史数据
        """
        return WebAction().api_action(cmd='get_site_history', data=self.parser.parse_args())


@site.route('/statistics/seedinfo')
class SiteStatisticsSeedinfo(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('name', type=str, help='站点名称', location='form', required=True)

    @site.doc(parser=parser)
    def post(self):
        """
        查询站点做种分布
        """
        return WebAction().api_action(cmd='get_site_seeding_info', data=self.parser.parse_args())


@site.route('/resources')
class SiteResources(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, help='站点索引ID', location='form', required=True)
    parser.add_argument('page', type=int, help='页码', location='form')
    parser.add_argument('keyword', type=str, help='站点名称', location='form')

    @site.doc(parser=parser)
    def post(self):
        """
        查询站点资源列表
        """
        return WebAction().api_action(cmd='list_site_resources', data=self.parser.parse_args())


@search.route('/keyword')
class SearchKeyword(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('search_word', type=str, help='搜索关键字', location='form', required=True)
    parser.add_argument('unident', type=bool, help='快速模式', location='form')
    parser.add_argument('filters', type=str, help='过滤条件', location='form')
    parser.add_argument('tmdbid', type=str, help='TMDBID', location='form')
    parser.add_argument('media_type', type=str, help='类型（电影/电视剧）', location='form')

    @search.doc(parser=parser)
    def post(self):
        """
        根据关键字/TMDBID搜索
        """
        return WebAction().api_action(cmd='search', data=self.parser.parse_args())


@search.route('/result')
class SearchResult(ClientResource):
    @staticmethod
    def post(self):
        """
        查询搜索结果
        """
        return WebAction().api_action(cmd='get_search_result')


@download.route('/search')
class DownloadSearch(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, help='搜索结果ID', location='form', required=True)
    parser.add_argument('dir', type=str, help='下载目录', location='form')

    @download.doc(parser=parser)
    def post(self):
        """
        下载搜索结果
        """
        return WebAction().api_action(cmd='download', data=self.parser.parse_args())


@download.route('/item')
class DownloadItem(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('enclosure', type=str, help='链接URL', location='form', required=True)
    parser.add_argument('title', type=str, help='标题', location='form', required=True)
    parser.add_argument('site', type=str, help='站点名称', location='form')
    parser.add_argument('description', type=str, help='描述', location='form')
    parser.add_argument('page_url', type=str, help='详情页面URL', location='form')
    parser.add_argument('size', type=str, help='大小', location='form')
    parser.add_argument('seeders', type=str, help='做种数', location='form')
    parser.add_argument('uploadvolumefactor', type=float, help='上传因子', location='form')
    parser.add_argument('downloadvolumefactor', type=float, help='下载因子', location='form')
    parser.add_argument('dl_dir', type=str, help='保存目录', location='form')

    @download.doc(parser=parser)
    def post(self):
        """
        下载链接
        """
        return WebAction().api_action(cmd='download_link', data=self.parser.parse_args())


@download.route('/start')
class DownloadStart(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, help='任务ID', location='form', required=True)

    @download.doc(parser=parser)
    def post(self):
        """
        开始下载任务
        """
        return WebAction().api_action(cmd='pt_start', data=self.parser.parse_args())


@download.route('/stop')
class DownloadStop(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, help='任务ID', location='form', required=True)

    @download.doc(parser=parser)
    def post(self):
        """
        暂停下载任务
        """
        return WebAction().api_action(cmd='pt_stop', data=self.parser.parse_args())


@download.route('/info')
class DownloadInfo(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('ids', type=str, help='任务IDS', location='form', required=True)

    @download.doc(parser=parser)
    def post(self):
        """
        查询下载进度
        """
        return WebAction().api_action(cmd='pt_info', data=self.parser.parse_args())


@download.route('/remove')
class DownloadRemove(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, help='任务ID', location='form', required=True)

    @download.doc(parser=parser)
    def post(self):
        """
        删除下载任务
        """
        return WebAction().api_action(cmd='pt_remove', data=self.parser.parse_args())


@download.route('/history')
class DownloadHistory(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('page', type=str, help='第几页', location='form', required=True)

    @download.doc(parser=parser)
    def post(self):
        """
        查询下载历史
        """
        return WebAction().api_action(cmd='get_downloaded', data=self.parser.parse_args())


@organization.route('/unknown/delete')
class UnknownDelete(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, help='未识别记录ID', location='form', required=True)

    @organization.doc(parser=parser)
    def post(self):
        """
        删除未识别记录
        """
        return WebAction().api_action(cmd='del_unknown_path', data=self.parser.parse_args())


@organization.route('/unknown/rename')
class UnknownRename(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('logid', type=str, help='转移历史记录ID', location='form')
    parser.add_argument('unknown_id', type=str, help='未识别记录ID', location='form')
    parser.add_argument('syncmod', type=str, help='转移模式', location='form', required=True)
    parser.add_argument('tmdb', type=int, help='TMDB ID', location='form')
    parser.add_argument('title', type=str, help='标题', location='form')
    parser.add_argument('year', type=str, help='年份', location='form')
    parser.add_argument('type', type=str, help='类型（MOV/TV/ANIME）', location='form')
    parser.add_argument('season', type=int, help='季号', location='form')
    parser.add_argument('episode_format', type=str, help='集数定位', location='form')
    parser.add_argument('min_filesize', type=int, help='最小文件大小', location='form')

    @organization.doc(parser=parser)
    def post(self):
        """
        手动识别
        """
        return WebAction().api_action(cmd='rename', data=self.parser.parse_args())


@organization.route('/unknown/renameudf')
class UnknownRenameUDF(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('inpath', type=str, help='源目录', location='form', required=True)
    parser.add_argument('outpath', type=str, help='目的目录', location='form', required=True)
    parser.add_argument('syncmod', type=str, help='转移模式', location='form', required=True)
    parser.add_argument('tmdb', type=int, help='TMDB ID', location='form')
    parser.add_argument('title', type=str, help='标题', location='form')
    parser.add_argument('year', type=str, help='年份', location='form')
    parser.add_argument('type', type=str, help='类型（MOV/TV/ANIME）', location='form')
    parser.add_argument('season', type=int, help='季号', location='form')
    parser.add_argument('episode_format', type=str, help='集数定位', location='form')
    parser.add_argument('episode_details', type=str, help='集数范围', location='form')
    parser.add_argument('episode_offset', type=str, help='集数偏移', location='form')
    parser.add_argument('min_filesize', type=int, help='最小文件大小', location='form')

    @organization.doc(parser=parser)
    def post(self):
        """
        自定义识别
        """
        return WebAction().api_action(cmd='rename_udf', data=self.parser.parse_args())


@organization.route('/unknown/redo')
class UnknownRedo(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('flag', type=str, help='类型（unknow/history）', location='form', required=True)
    parser.add_argument('ids', type=list, help='记录ID', location='form', required=True)

    @organization.doc(parser=parser)
    def post(self):
        """
        重新识别
        """
        return WebAction().api_action(cmd='re_identification', data=self.parser.parse_args())


@organization.route('/history/delete')
class TransferHistoryDelete(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('logids', type=list, help='记录IDS', location='form', required=True)

    @organization.doc(parser=parser)
    def post(self):
        """
        删除媒体整理历史记录
        """
        return WebAction().api_action(cmd='delete_history', data=self.parser.parse_args())


@organization.route('/history/statistics')
class HistoryStatistics(ClientResource):

    @staticmethod
    def post():
        """
        查询转移历史统计数据
        """
        return WebAction().api_action(cmd='get_transfer_statistics')


@organization.route('/cache/empty')
class TransferCacheEmpty(ClientResource):

    @staticmethod
    def post():
        """
        清空文件转移缓存
        """
        return WebAction().api_action(cmd='truncate_blacklist')


@library.route('/library/start')
class LibrarySyncStart(ClientResource):

    @staticmethod
    def post():
        """
        开始媒体库同步
        """
        return WebAction().api_action(cmd='start_mediasync')


@library.route('/library/status')
class LibrarySyncStatus(ClientResource):

    @staticmethod
    def post():
        """
        查询媒体库同步状态
        """
        return WebAction().api_action(cmd='mediasync_state')


@library.route('/library/playhistory')
class LibraryPlayHistory(ClientResource):

    @staticmethod
    def post():
        """
        查询媒体库播放历史
        """
        return WebAction().api_action(cmd='get_library_playhistory')


@library.route('/library/statistics')
class LibraryStatistics(ClientResource):

    @staticmethod
    def post():
        """
        查询媒体库统计数据
        """
        return WebAction().api_action(cmd="get_library_mediacount")


@library.route('/library/space')
class LibrarySpace(ClientResource):

    @staticmethod
    def post():
        """
        查询媒体库存储空间
        """
        return WebAction().api_action(cmd='get_library_spacesize')


@system.route('/logging')
class SystemLogging(ClientResource):

    @staticmethod
    def post():
        """
        获取实时日志
        """
        return WebAction().api_action(cmd='logging')


@system.route('/version')
class SystemVersion(ClientResource):

    @staticmethod
    def post():
        """
        查询最新版本号
        """
        return WebAction().api_action(cmd='version')


@system.route('/restart')
class SystemRestart(ClientResource):

    @staticmethod
    def post():
        """
        重启
        """
        return WebAction().api_action(cmd='restart')


@system.route('/update')
class SystemUpdate(ClientResource):

    @staticmethod
    def post():
        """
        升级
        """
        return WebAction().api_action(cmd='update_system')


@system.route('/logout')
class SystemUpdate(ClientResource):

    @staticmethod
    def post():
        """
        注销
        """
        token = request.headers.get("Authorization", default=None)
        if token:
            TokenCache.delete(token)
        return {
            "code": 0,
            "success": True
        }


@system.route('/message')
class SystemMessage(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('lst_time', type=str, help='时间（YYYY-MM-DD HH24:MI:SS）', location='form')

    @system.doc(parser=parser)
    def post(self):
        """
        查询消息中心消息
        """
        return WebAction().get_system_message(lst_time=self.parser.parse_args().get("lst_time"))


@system.route('/progress')
class SystemProgress(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('type', type=str, help='类型（search/mediasync）', location='form', required=True)

    @system.doc(parser=parser)
    def post(self):
        """
        查询搜索/媒体同步等进度
        """
        return WebAction().api_action(cmd='refresh_process', data=self.parser.parse_args())


@config.route('/update')
class ConfigUpdate(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('items', type=dict, help='配置项', location='form', required=True)

    def post(self):
        """
        新增/修改配置
        """
        return WebAction().api_action(cmd='update_config', data=self.parser.parse_args().get("items"))


@config.route('/test')
class ConfigTest(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('command', type=str, help='测试命令', location='form', required=True)

    @config.doc(parser=parser)
    def post(self):
        """
        测试配置连通性
        """
        return WebAction().api_action(cmd='test_connection', data=self.parser.parse_args())


@config.route('/restore')
class ConfigRestore(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('file_name', type=str, help='备份文件名', location='form', required=True)

    @config.doc(parser=parser)
    def post(self):
        """
        恢复备份的配置
        """
        return WebAction().api_action(cmd='restory_backup', data=self.parser.parse_args())


@subscribe.route('/delete')
class SubscribeDelete(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('name', type=str, help='名称', location='form')
    parser.add_argument('type', type=str, help='类型（MOV/TV）', location='form')
    parser.add_argument('year', type=str, help='发行年份', location='form')
    parser.add_argument('season', type=int, help='季号', location='form')
    parser.add_argument('rssid', type=int, help='已有订阅ID', location='form')
    parser.add_argument('tmdbid', type=str, help='TMDBID', location='form')

    @subscribe.doc(parser=parser)
    def post(self):
        """
        删除订阅
        """
        return WebAction().api_action(cmd='remove_rss_media', data=self.parser.parse_args())


@subscribe.route('/add')
class SubscribeAdd(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('name', type=str, help='名称', location='form', required=True)
    parser.add_argument('type', type=str, help='类型（MOV/TV）', location='form', required=True)
    parser.add_argument('year', type=str, help='发行年份', location='form')
    parser.add_argument('season', type=int, help='季号', location='form')
    parser.add_argument('rssid', type=int, help='已有订阅ID', location='form')
    parser.add_argument('tmdbid', type=str, help='TMDBID', location='form')
    parser.add_argument('doubanid', type=str, help='豆瓣ID', location='form')
    parser.add_argument('match', type=bool, help='模糊匹配', location='form')
    parser.add_argument('sites', type=list, help='RSS站点', location='form')
    parser.add_argument('search_sites', type=list, help='搜索站点', location='form')
    parser.add_argument('over_edition', type=bool, help='洗版', location='form')
    parser.add_argument('rss_restype', type=str, help='资源类型', location='form')
    parser.add_argument('rss_pix', type=str, help='分辨率', location='form')
    parser.add_argument('rss_team', type=str, help='字幕组/发布组', location='form')
    parser.add_argument('rss_rule', type=str, help='过滤规则', location='form')
    parser.add_argument('total_ep', type=int, help='总集数', location='form')
    parser.add_argument('current_ep', type=int, help='开始集数', location='form')

    @subscribe.doc(parser=parser)
    def post(self):
        """
        新增/修改订阅
        """
        return WebAction().api_action(cmd='add_rss_media', data=self.parser.parse_args())


@subscribe.route('/movie/date')
class SubscribeMovieDate(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, help='TMDBID/DB:豆瓣ID', location='form', required=True)

    @subscribe.doc(parser=parser)
    def post(self):
        """
        电影上映日期
        """
        return WebAction().api_action(cmd='movie_calendar_data', data=self.parser.parse_args())


@subscribe.route('/tv/date')
class SubscribeTVDate(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, help='TMDBID/DB:豆瓣ID', location='form', required=True)
    parser.add_argument('season', type=int, help='季号', location='form', required=True)
    parser.add_argument('name', type=str, help='名称', location='form')

    @subscribe.doc(parser=parser)
    def post(self):
        """
        电视剧上映日期
        """
        return WebAction().api_action(cmd='tv_calendar_data', data=self.parser.parse_args())


@subscribe.route('/search')
class SubscribeSearch(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('type', type=str, help='类型（MOV/TV）', location='form', required=True)
    parser.add_argument('rssid', type=int, help='订阅ID', location='form', required=True)

    @subscribe.doc(parser=parser)
    def post(self):
        """
        订阅搜索
        """
        return WebAction().api_action(cmd='refresh_rss', data=self.parser.parse_args())


@subscribe.route('/info')
class SubscribeInfo(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('rssid', type=int, help='订阅ID', location='form', required=True)
    parser.add_argument('type', type=str, help='订阅类型（MOV/TV）', location='form', required=True)

    @subscribe.doc(parser=parser)
    def post(self):
        """
        订阅详情
        """
        return WebAction().api_action(cmd='rss_detail', data=self.parser.parse_args())


@subscribe.route('/redo')
class SubscribeRedo(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('rssid', type=int, help='订阅历史ID', location='form', required=True)
    parser.add_argument('type', type=str, help='订阅类型（MOV/TV）', location='form', required=True)

    @subscribe.doc(parser=parser)
    def post(self):
        """
        历史重新订阅
        """
        return WebAction().api_action(cmd='re_rss_history', data=self.parser.parse_args())


@subscribe.route('/history/delete')
class SubscribeHistoryDelete(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('rssid', type=int, help='订阅ID', location='form', required=True)

    @subscribe.doc(parser=parser)
    def post(self):
        """
        删除订阅历史
        """
        return WebAction().api_action(cmd='delete_rss_history', data=self.parser.parse_args())


@subscribe.route('/cache/delete')
class SubscribeCacheDelete(ClientResource):
    @staticmethod
    def post():
        """
        清理订阅缓存
        """
        return WebAction().api_action(cmd='truncate_rsshistory')


@recommend.route('/list')
class RecommendList(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('type', type=str,
                        help='类型（hm/ht/nm/nt/dbom/dbhm/dbht/dbdh/dbnm/dbtop/dbzy）',
                        location='form', required=True)
    parser.add_argument('page', type=int, help='页码', location='form', required=True)

    @recommend.doc(parser=parser)
    def post(self):
        """
        推荐列表
        """
        return WebAction().api_action(cmd='get_recommend', data=self.parser.parse_args())


@rss.route('/info')
class RssInfo(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='任务ID', location='form', required=True)

    @rss.doc(parser=parser)
    def post(self):
        """
        自定义订阅任务详情
        """
        return WebAction().api_action(cmd='get_userrss_task', data=self.parser.parse_args())


@rss.route('/delete')
class RssDelete(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='任务ID', location='form', required=True)

    @rss.doc(parser=parser)
    def post(self):
        """
        删除自定义订阅任务
        """
        return WebAction().api_action(cmd='delete_userrss_task', data=self.parser.parse_args())


@rss.route('/update')
class RssUpdate(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='任务ID', location='form')
    parser.add_argument('name', type=str, help='任务名称', location='form', required=True)
    parser.add_argument('address', type=str, help='RSS地址', location='form', required=True)
    parser.add_argument('parser', type=int, help='解析器ID', location='form', required=True)
    parser.add_argument('interval', type=int, help='刷新间隔（分钟）', location='form', required=True)
    parser.add_argument('uses', type=str, help='动作', location='form', required=True)
    parser.add_argument('state', type=str, help='状态（Y/N）', location='form', required=True)
    parser.add_argument('include', type=str, help='包含', location='form')
    parser.add_argument('exclude', type=str, help='排除', location='form')
    parser.add_argument('filterrule', type=int, help='过滤规则', location='form')
    parser.add_argument('note', type=str, help='备注', location='form')

    @rss.doc(parser=parser)
    def post(self):
        """
        新增/修改自定义订阅任务
        """
        return WebAction().api_action(cmd='update_userrss_task', data=self.parser.parse_args())


@rss.route('/parser/info')
class RssParserInfo(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='解析器ID', location='form', required=True)

    @rss.doc(parser=parser)
    def post(self):
        """
        解析器详情
        """
        return WebAction().api_action(cmd='get_rssparser', data=self.parser.parse_args())


@rss.route('/parser/delete')
class RssParserDelete(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='解析器ID', location='form', required=True)

    @rss.doc(parser=parser)
    def post(self):
        """
        删除解析器
        """
        return WebAction().api_action(cmd='delete_rssparser', data=self.parser.parse_args())


@rss.route('/parser/update')
class RssParserUpdate(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='解析器ID', location='form', required=True)
    parser.add_argument('name', type=str, help='名称', location='form', required=True)
    parser.add_argument('type', type=str, help='类型（JSON/XML）', location='form', required=True)
    parser.add_argument('format', type=str, help='解析格式', location='form', required=True)
    parser.add_argument('params', type=str, help='附加参数', location='form')

    @rss.doc(parser=parser)
    def post(self):
        """
        新增/修改解析器
        """
        return WebAction().api_action(cmd='update_rssparser', data=self.parser.parse_args())


@rss.route('/run')
class RssRun(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='任务ID', location='form', required=True)

    @rss.doc(parser=parser)
    def post(self):
        """
        运行自定义订阅任务
        """
        return WebAction().api_action(cmd='run_userrss', data=self.parser.parse_args())


@rss.route('/preview')
class RssPreview(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='任务ID', location='form', required=True)

    @rss.doc(parser=parser)
    def post(self):
        """
        自定义订阅预览
        """
        return WebAction().api_action(cmd='list_rss_articles', data=self.parser.parse_args())


@rss.route('/name/test')
class RssNameTest(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('taskid', type=int, help='任务ID', location='form', required=True)
    parser.add_argument('title', type=str, help='名称', location='form', required=True)

    @rss.doc(parser=parser)
    def post(self):
        """
        自定义订阅名称测试
        """
        return WebAction().api_action(cmd='rss_article_test', data=self.parser.parse_args())


@rss.route('/item/history')
class RssItemHistory(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='任务ID', location='form', required=True)

    @rss.doc(parser=parser)
    def post(self):
        """
        自定义订阅任务条目处理记录
        """
        return WebAction().api_action(cmd='list_rss_history', data=self.parser.parse_args())


@rss.route('/item/set')
class RssItemSet(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('flag', type=str, help='操作类型（set_finished/set_unfinish）', location='form', required=True)
    parser.add_argument('articles', type=list, help='条目（{title/enclosure}）', location='form', required=True)

    @rss.doc(parser=parser)
    def post(self):
        """
        自定义订阅任务条目状态调整
        """
        return WebAction().api_action(cmd='rss_articles_check', data=self.parser.parse_args())


@rss.route('/item/download')
class RssItemDownload(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('taskid', type=int, help='任务ID', location='form', required=True)
    parser.add_argument('articles', type=list, help='条目（{title/enclosure}）', location='form', required=True)

    @rss.doc(parser=parser)
    def post(self):
        """
        自定义订阅任务条目下载
        """
        return WebAction().api_action(cmd='rss_articles_download', data=self.parser.parse_args())


@media.route('/cache/update')
class MediaCacheUpdate(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('key', type=str, help='缓存Key值', location='form', required=True)
    parser.add_argument('title', type=str, help='标题', location='form', required=True)

    @media.doc(parser=parser)
    def post(self):
        """
        修改TMDB缓存标题
        """
        return WebAction().api_action(cmd='modify_tmdb_cache', data=self.parser.parse_args())


@media.route('/cache/delete')
class MediaCacheDelete(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('cache_key', type=str, help='缓存Key值', location='form', required=True)

    @media.doc(parser=parser)
    def post(self):
        """
        删除TMDB缓存
        """
        return WebAction().api_action(cmd='delete_tmdb_cache', data=self.parser.parse_args())


@media.route('/cache/clear')
class MediaCacheClear(ClientResource):

    @staticmethod
    def post():
        """
        清空TMDB缓存
        """
        return WebAction().api_action(cmd='clear_tmdb_cache')


@media.route('/tv/seasons')
class MediaTvSeasons(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('tmdbid', type=str, help='TMDBID', location='form', required=True)

    @media.doc(parser=parser)
    def post(self):
        """
        查询电视剧季列表
        """
        return WebAction().api_action(cmd='get_tvseason_list', data=self.parser.parse_args())


@media.route('/category/list')
class MediaCategoryList(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('type', type=str, help='类型（电影/电视剧/动漫）', location='form', required=True)

    @media.doc(parser=parser)
    def post(self):
        """
        查询二级分类配置
        """
        return WebAction().api_action(cmd='get_categories', data=self.parser.parse_args())


@media.route('/info')
class MediaInfo(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('type', type=str, help='类型（MOV/TV）', location='form', required=True)
    parser.add_argument('id', type=str, help='TMDBID', location='form')
    parser.add_argument('doubanid', type=str, help='豆瓣ID', location='form')
    parser.add_argument('title', type=str, help='标题', location='form')
    parser.add_argument('year', type=str, help='年份', location='form')
    parser.add_argument('rssid', type=str, help='订阅ID', location='form')

    @media.doc(parser=parser)
    def post(self):
        """
        识别媒体信息
        """
        return WebAction().api_action(cmd='media_info', data=self.parser.parse_args())


@brushtask.route('/update')
class BrushTaskUpdate(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('brushtask_id', type=str, help='刷流任务ID', location='form')
    parser.add_argument('brushtask_name', type=str, help='任务名称', location='form', required=True)
    parser.add_argument('brushtask_site', type=int, help='站点', location='form', required=True)
    parser.add_argument('brushtask_interval', type=int, help='刷新间隔(分钟)', location='form', required=True)
    parser.add_argument('brushtask_downloader', type=int, help='下载器', location='form', required=True)
    parser.add_argument('brushtask_totalsize', type=int, help='保种体积(GB)', location='form', required=True)
    parser.add_argument('brushtask_state', type=str, help='状态（Y/N）', location='form', required=True)
    parser.add_argument('brushtask_transfer', type=str, help='转移到媒体库（Y/N）', location='form')
    parser.add_argument('brushtask_sendmessage', type=str, help='消息推送（Y/N）', location='form')
    parser.add_argument('brushtask_forceupload', type=str, help='强制做种（Y/N）', location='form')
    parser.add_argument('brushtask_free', type=str, help='促销（FREE/2XFREE）', location='form')
    parser.add_argument('brushtask_hr', type=str, help='Hit&Run（HR）', location='form')
    parser.add_argument('brushtask_torrent_size', type=int, help='种子大小(GB)', location='form')
    parser.add_argument('brushtask_include', type=str, help='包含', location='form')
    parser.add_argument('brushtask_exclude', type=str, help='排除', location='form')
    parser.add_argument('brushtask_dlcount', type=int, help='同时下载任务数', location='form')
    parser.add_argument('brushtask_peercount', type=int, help='做种人数限制', location='form')
    parser.add_argument('brushtask_seedtime', type=float, help='做种时间(小时)', location='form')
    parser.add_argument('brushtask_seedratio', type=float, help='分享率', location='form')
    parser.add_argument('brushtask_seedsize', type=int, help='上传量(GB)', location='form')
    parser.add_argument('brushtask_dltime', type=float, help='下载耗时(小时)', location='form')
    parser.add_argument('brushtask_avg_upspeed', type=int, help='平均上传速度(KB/S)', location='form')
    parser.add_argument('brushtask_pubdate', type=int, help='发布时间（小时）', location='form')
    parser.add_argument('brushtask_upspeed', type=int, help='上传限速（KB/S）', location='form')
    parser.add_argument('brushtask_downspeed', type=int, help='下载限速（KB/S）', location='form')

    @brushtask.doc(parser=parser)
    def post(self):
        """
        新增/修改刷流任务
        """
        return WebAction().api_action(cmd='add_brushtask', data=self.parser.parse_args())


@brushtask.route('/delete')
class BrushTaskDelete(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, help='刷流任务ID', location='form', required=True)

    @brushtask.doc(parser=parser)
    def post(self):
        """
        删除刷流任务
        """
        return WebAction().api_action(cmd='del_brushtask', data=self.parser.parse_args())


@brushtask.route('/info')
class BrushTaskInfo(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, help='刷流任务ID', location='form', required=True)

    @brushtask.doc(parser=parser)
    def post(self):
        """
        刷流任务详情
        """
        return WebAction().api_action(cmd='brushtask_detail', data=self.parser.parse_args())


@brushtask.route('/downloader/update')
class BrushTaskDownloaderUpdate(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('test', type=bool, help='测试', location='form', required=True)
    parser.add_argument('id', type=int, help='下载器ID', location='form')
    parser.add_argument('name', type=str, help='名称', location='form', required=True)
    parser.add_argument('type', type=str, help='类型（qbittorrent/transmission）', location='form', required=True)
    parser.add_argument('host', type=str, help='地址', location='form', required=True)
    parser.add_argument('port', type=int, help='端口', location='form', required=True)
    parser.add_argument('username', type=str, help='用户名', location='form')
    parser.add_argument('password', type=str, help='密码', location='form')
    parser.add_argument('save_dir', type=str, help='保存目录', location='form')

    @brushtask.doc(parser=parser)
    def post(self):
        """
        新增/修改刷流下载器
        """
        return WebAction().api_action(cmd='add_downloader', data=self.parser.parse_args())


@brushtask.route('/downloader/delete')
class BrushTaskDownloaderDelete(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='下载器ID', location='form', required=True)

    @brushtask.doc(parser=parser)
    def post(self):
        """
        删除刷流下载器
        """
        return WebAction().api_action(cmd='delete_downloader', data=self.parser.parse_args())


@brushtask.route('/downloader/info')
class BrushTaskDownloaderInfo(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='下载器ID', location='form', required=True)

    @brushtask.doc(parser=parser)
    def post(self):
        """
        刷流下载器详情
        """
        return WebAction().api_action(cmd='get_downloader', data=self.parser.parse_args())


@brushtask.route('/run')
class BrushTaskRun(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='刷流任务ID', location='form', required=True)

    @brushtask.doc(parser=parser)
    def post(self):
        """
        刷流下载器详情
        """
        return WebAction().api_action(cmd='run_brushtask', data=self.parser.parse_args())


@filterrule.route('/group/add')
class FilterRuleGroupAdd(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('name', type=str, help='名称', location='form', required=True)
    parser.add_argument('default', type=str, help='默认（Y/N）', location='form', required=True)

    @filterrule.doc(parser=parser)
    def post(self):
        """
        新增规则组
        """
        return WebAction().api_action(cmd='add_filtergroup', data=self.parser.parse_args())


@filterrule.route('/group/restore')
class FilterRuleGroupRestore(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('groupids', type=list, help='规则组ID', location='form', required=True)
    parser.add_argument('init_rulegroups', type=list, help='规则组脚本', location='form', required=True)

    @filterrule.doc(parser=parser)
    def post(self):
        """
        恢复默认规则组
        """
        return WebAction().api_action(cmd='restore_filtergroup', data=self.parser.parse_args())


@filterrule.route('/group/default')
class FilterRuleGroupDefault(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, help='规则组ID', location='form', required=True)

    @filterrule.doc(parser=parser)
    def post(self):
        """
        设置默认规则组
        """
        return WebAction().api_action(cmd='set_default_filtergroup', data=self.parser.parse_args())


@filterrule.route('/group/delete')
class FilterRuleGroupDelete(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=str, help='规则组ID', location='form', required=True)

    @filterrule.doc(parser=parser)
    def post(self):
        """
        删除规则组
        """
        return WebAction().api_action(cmd='del_filtergroup', data=self.parser.parse_args())


@filterrule.route('/rule/update')
class FilterRuleUpdate(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('rule_id', type=int, help='规则ID', location='form')
    parser.add_argument('group_id', type=int, help='规则组ID', location='form', required=True)
    parser.add_argument('rule_name', type=str, help='规则名称', location='form', required=True)
    parser.add_argument('rule_pri', type=str, help='优先级', location='form', required=True)
    parser.add_argument('rule_include', type=str, help='包含', location='form')
    parser.add_argument('rule_exclude', type=str, help='排除', location='form')
    parser.add_argument('rule_sizelimit', type=str, help='大小限制', location='form')
    parser.add_argument('rule_free', type=str, help='促销（FREE/2XFREE）', location='form')

    @filterrule.doc(parser=parser)
    def post(self):
        """
        新增/修改规则
        """
        return WebAction().api_action(cmd='add_filterrule', data=self.parser.parse_args())


@filterrule.route('/rule/delete')
class FilterRuleDelete(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='规则ID', location='form', required=True)

    @filterrule.doc(parser=parser)
    def post(self):
        """
        删除规则
        """
        return WebAction().api_action(cmd='del_filterrule', data=self.parser.parse_args())


@filterrule.route('/rule/info')
class FilterRuleInfo(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('ruleid', type=int, help='规则ID', location='form', required=True)
    parser.add_argument('groupid', type=int, help='规则组ID', location='form', required=True)

    @filterrule.doc(parser=parser)
    def post(self):
        """
        规则详情
        """
        return WebAction().api_action(cmd='filterrule_detail', data=self.parser.parse_args())


@filterrule.route('/rule/share')
class FilterRuleShare(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='规则组ID', location='form', required=True)

    @filterrule.doc(parser=parser)
    def post(self):
        """
        分享规则组
        """
        return WebAction().api_action(cmd='share_filtergroup', data=self.parser.parse_args())


@filterrule.route('/rule/import')
class FilterRuleImport(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('content', type=str, help='规则内容', location='form', required=True)

    @filterrule.doc(parser=parser)
    def post(self):
        """
        导入规则组
        """
        return WebAction().api_action(cmd='import_filtergroup', data=self.parser.parse_args())


@words.route('/group/add')
class WordsGroupAdd(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('tmdb_id', type=str, help='TMDBID', location='form', required=True)
    parser.add_argument('tmdb_type', type=str, help='类型（movie/tv）', location='form', required=True)

    @words.doc(parser=parser)
    def post(self):
        """
        新增识别词组
        """
        return WebAction().api_action(cmd='add_custom_word_group', data=self.parser.parse_args())


@words.route('/group/delete')
class WordsGroupDelete(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('gid', type=int, help='识别词组ID', location='form', required=True)

    @words.doc(parser=parser)
    def post(self):
        """
        删除识别词组
        """
        return WebAction().api_action(cmd='delete_custom_word_group', data=self.parser.parse_args())


@words.route('/item/update')
class WordItemUpdate(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='识别词ID', location='form', required=True)
    parser.add_argument('gid', type=int, help='识别词组ID', location='form', required=True)
    parser.add_argument('group_type', type=str, help='媒体类型（1/2）', location='form', required=True)
    parser.add_argument('new_replaced', type=str, help='被替换词', location='form')
    parser.add_argument('new_replace', type=str, help='替换词', location='form')
    parser.add_argument('new_front', type=str, help='前定位词', location='form')
    parser.add_argument('new_back', type=str, help='后定位词', location='form')
    parser.add_argument('new_offset', type=str, help='偏移集数', location='form')
    parser.add_argument('new_help', type=str, help='备注', location='form')
    parser.add_argument('type', type=str, help='识别词类型（1/2/3/4）', location='form', required=True)
    parser.add_argument('season', type=str, help='季', location='form')
    parser.add_argument('enabled', type=str, help='状态（1/0）', location='form', required=True)
    parser.add_argument('regex', type=str, help='正则表达式（1/0）', location='form')

    @words.doc(parser=parser)
    def post(self):
        """
        新增/修改识别词
        """
        return WebAction().api_action(cmd='add_or_edit_custom_word', data=self.parser.parse_args())


@words.route('/item/info')
class WordItemInfo(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('wid', type=int, help='识别词ID', location='form', required=True)

    @words.doc(parser=parser)
    def post(self):
        """
        识别词详情
        """
        return WebAction().api_action(cmd='get_custom_word', data=self.parser.parse_args())


@words.route('/item/delete')
class WordItemDelete(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='识别词ID', location='form', required=True)

    @words.doc(parser=parser)
    def post(self):
        """
        删除识别词
        """
        return WebAction().api_action(cmd='delete_custom_word', data=self.parser.parse_args())


@words.route('/item/status')
class WordItemStatus(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('ids_info', type=list, help='识别词IDS', location='form', required=True)
    parser.add_argument('flag', type=int, help='状态（1/0）', location='form', required=True)

    @words.doc(parser=parser)
    def post(self):
        """
        设置识别词状态
        """
        return WebAction().api_action(cmd='check_custom_words', data=self.parser.parse_args())


@words.route('/item/export')
class WordItemExport(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('note', type=str, help='备注', location='form', required=True)
    parser.add_argument('ids_info', type=str, help='识别词IDS（@_）', location='form', required=True)

    @words.doc(parser=parser)
    def post(self):
        """
        导出识别词
        """
        return WebAction().api_action(cmd='export_custom_words', data=self.parser.parse_args())


@words.route('/item/analyse')
class WordItemAnalyse(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('import_code', type=str, help='识别词代码', location='form', required=True)

    @words.doc(parser=parser)
    def post(self):
        """
        分析识别词
        """
        return WebAction().api_action(cmd='analyse_import_custom_words_code', data=self.parser.parse_args())


@words.route('/item/import')
class WordItemImport(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('import_code', type=str, help='识别词代码', location='form', required=True)
    parser.add_argument('ids_info', type=list, help='识别词IDS', location='form', required=True)

    @words.doc(parser=parser)
    def post(self):
        """
        分析识别词
        """
        return WebAction().api_action(cmd='import_custom_words', data=self.parser.parse_args())


@sync.route('/directory/update')
class SyncDirectoryUpdate(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('sid', type=int, help='同步目录ID', location='form')
    parser.add_argument('from', type=str, help='源目录', location='form', required=True)
    parser.add_argument('to', type=str, help='目的目录', location='form')
    parser.add_argument('unknown', type=str, help='未知目录', location='form')
    parser.add_argument('syncmod', type=str, help='同步模式', location='form')
    parser.add_argument('rename', type=bool, help='重命名', location='form')
    parser.add_argument('enabled', type=bool, help='开启', location='form')

    @sync.doc(parser=parser)
    def post(self):
        """
        新增/修改同步目录
        """
        return WebAction().api_action(cmd='add_or_edit_sync_path', data=self.parser.parse_args())


@sync.route('/directory/info')
class SyncDirectoryInfo(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('sid', type=int, help='同步目录ID', location='form', required=True)

    @sync.doc(parser=parser)
    def post(self):
        """
        同步目录详情
        """
        return WebAction().api_action(cmd='get_sync_path', data=self.parser.parse_args())


@sync.route('/directory/delete')
class SyncDirectoryDelete(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('sid', type=int, help='同步目录ID', location='form', required=True)

    @sync.doc(parser=parser)
    def post(self):
        """
        删除同步目录
        """
        return WebAction().api_action(cmd='delete_sync_path', data=self.parser.parse_args())


@sync.route('/directory/status')
class SyncDirectoryStatus(ClientResource):
    parser = reqparse.RequestParser()
    parser.add_argument('sid', type=int, help='同步目录ID', location='form', required=True)
    parser.add_argument('flag', type=int, help='操作（rename/enable）', location='form', required=True)
    parser.add_argument('checked', type=bool, help='状态', location='form', required=True)

    @sync.doc(parser=parser)
    def post(self):
        """
        设置同步目录状态
        """
        return WebAction().api_action(cmd='check_sync_path', data=self.parser.parse_args())
