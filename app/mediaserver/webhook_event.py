import time

from app.message.message import Message
from app.mediaserver.media_server import MediaServer
from app.filetransfer import FileTransfer
from app.utils import WebUtils


class WebhookEvent:
    __json = None
    message = None
    mediaserver = None
    filetransfer = None

    def __init__(self):
        self.message = Message()
        self.mediaserver = MediaServer()
        self.filetransfer = FileTransfer()

    @staticmethod
    def __parse_plex_msg(message):
        """
        解析Plex报文
        """
        eventItem = {'event': message.get('event', {}),
                     'item_name': message.get('Metadata', {}).get('title'),
                     'user_name': message.get('Account', {}).get('title')
                     }
        return eventItem

    @staticmethod
    def __parse_jellyfin_msg(message):
        """
        解析Jellyfin报文
        """
        eventItem = {'event': message.get('NotificationType', {}),
                     'item_name': message.get('Name'),
                     'user_name': message.get('NotificationUsername')
                     }
        return eventItem

    @staticmethod
    def __parse_emby_msg(message):
        """
        解析Emby报文
        """
        eventItem = {'event': message.get('Event', {})}
        if message.get('Item'):
            if message.get('Item', {}).get('Type') == 'Episode':
                eventItem['item_type'] = "TV"
                eventItem['item_name'] = "%s %s" % (
                    message.get('Item', {}).get('SeriesName'), message.get('Item', {}).get('Name'))
                eventItem['item_id'] = message.get('Item', {}).get('SeriesId')
                eventItem['tmdb_id'] = message.get('Item', {}).get('ProviderIds', {}).get('Tmdb')
            else:
                eventItem['item_type'] = "MOV"
                eventItem['item_name'] = message.get('Item', {}).get('Name')
                eventItem['item_path'] = message.get('Item', {}).get('Path')
                eventItem['item_id'] = message.get('Item', {}).get('Id')
                eventItem['tmdb_id'] = message.get('Item', {}).get('ProviderIds', {}).get('Tmdb')
        if message.get('Session'):
            eventItem['ip'] = message.get('Session').get('RemoteEndPoint')
            eventItem['device_name'] = message.get('Session').get('DeviceName')
            eventItem['client'] = message.get('Session').get('Client')
        if message.get("User"):
            eventItem['user_name'] = message.get("User").get('Name')

        return eventItem

    def plex_action(self, message):
        """
        执行Plex webhook动作
        """
        event_info = self.__parse_plex_msg(message)
        if event_info.get("event") in ["media.play", "media.stop"]:
            self.send_webhook_message(event_info, 'plex')

    def jellyfin_action(self, message):
        """
        执行Jellyfin webhook动作
        """
        event_info = self.__parse_jellyfin_msg(message)
        if event_info.get("event") in ["PlaybackStart", "PlaybackStop"]:
            self.send_webhook_message(event_info, 'jellyfin')

    def emby_action(self, message):
        """
        执行Emby webhook动作
        """
        event_info = self.__parse_emby_msg(message)
        if event_info.get("event") == "system.webhooktest":
            return
        elif event_info.get("event") in ["playback.start", "playback.stop"]:
            self.send_webhook_message(event_info, 'emby')
        elif event_info.get("event") == "item.rate":
            if event_info.get("item_path") and event_info.get('item_type') == "MOV":
                ret, _ = self.filetransfer.transfer_embyfav(event_info.get("item_path"))
                if ret:
                    # 刷新媒体库
                    self.mediaserver.refresh_root_library()

    def send_webhook_message(self, event_info, channel):
        """
        发送消息
        """
        _webhook_actions = {
            "system.webhooktest": "测试",
            "playback.start": "开始播放",
            "media.play": "开始播放",
            "PlaybackStart": "开始播放",
            "PlaybackStop": "停止播放",
            "playback.stop": "停止播放",
            "media.stop": "停止播放",
            "item.rate": "标记了",
        }
        _webhook_images = {
            "emby": "https://emby.media/notificationicon.png",
            "plex": "https://www.plex.tv/wp-content/uploads/2022/04/new-logo-process-lines-gray.png",
            "jellyfin": "https://play-lh.googleusercontent.com/SCsUK3hCCRqkJbmLDctNYCfehLxsS4ggD1ZPHIFrrAN1Tn9yhjmGMPep2D9lMaaa9eQi"
        }

        if self.is_ignore_webhook_message(event_info.get('user_name'), event_info.get('device_name')):
            return
        # 消息标题
        message_title = f"用户 {event_info.get('user_name')} {_webhook_actions.get(event_info.get('event'))} {event_info.get('item_name')}"
        # 消息内容
        message_texts = []
        if event_info.get('device_name'):
            message_texts.append(f"设备：{event_info.get('device_name')}")
        if event_info.get('client'):
            message_texts.append(f"客户端：{event_info.get('client')}")
        if event_info.get('ip'):
            message_texts.append(f"IP地址：{event_info.get('ip')}")
            message_texts.append(f"位置：{WebUtils.get_location(event_info.get('ip'))}")
        message_texts.append(f"时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}")
        # 消息图片
        if event_info.get('item_id'):
            image_url = self.mediaserver.get_image_by_id(event_info.get('item_id'), "Backdrop") or _webhook_images.get(
                channel)
        else:
            image_url = _webhook_images.get(channel)
        # 发送消息
        self.message.sendmsg(title=message_title, text="\n".join(message_texts), image=image_url)

    def is_ignore_webhook_message(self, user_name, device_name):
        """
        判断是否忽略通知
        """
        if not user_name and not device_name:
            return False
        webhook_ignore = self.message.get_webhook_ignore()
        if not webhook_ignore:
            return False
        if user_name in webhook_ignore or \
                device_name in webhook_ignore or \
                (user_name + ':' + device_name) in webhook_ignore:
            return True
        return False
