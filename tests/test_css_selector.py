import re
from datetime import datetime

from pyquery import PyQuery

from app.indexer.client._spider import TorrentSpider
from app.utils import ExceptionUtils

html = """
<tr data="72796">
    <td class="rowfollow nowrap" valign="middle"><a class="dib" href="https://www.pttime.org/torrents.php?cat=402"><img
            src="https://www.pttime.org/pic/trans.gif" alt="TV Series(电视剧)" title="TV Series(电视剧)"/><span
            class="category dib c_tvseries" alt="TV Series(电视剧)" title="TV Series(电视剧)"/></a></td>
    <td class="rowfollow" align="left">
        <table class="torrentname" width="100%">
            <tr>
                <td class="torrentimg"><img alt="/public/douban/5262275.jpg" referrer="no-referrer"
                                            onerror="imgError(this);" class="pr5"
                                            src="https://www.pttime.org/public/douban/5262275.jpg" height="52"
                                            onmouseover="showmenu(this,'tid_72796','/public/douban/5262275.jpg');"
                                            onmouseout="hiddmenu(this,'tid_72796');"/></td>
                <td class="embedded"><a title="How I Met Your Mother S06 2010 720p DSNP WEB-DL DDP 5.1 H.264-WhiteHat"
                                        target="_blank" class="torrentname_title"
                                        href="https://www.pttime.org/details.php?id=72796&amp;hit=1"><b
                        class="promotion free">How I Met Your Mother S06 2010 720p DSNP WEB-DL DDP 5.1
                    H.264-WhiteHat</b></a> <font class="promotion free">免费</font> <span title="2024-05-17 09:54:03">6天17时</span><br/><font
                        title="老爸老妈的浪漫史 第六季 / 老爸老妈罗曼史 第六季 / HIMYM 6">老爸老妈的浪漫史 第六季 /
                    老爸老妈罗曼史 第六季 / HIMYM 6</font></td>
                <td width="96" class="embedded" style="text-align: right; " valign="middle">
                    <table>
                        <tr>
                            <td class="embedded" width="60">
                                <div class="tar"><a target="_blank"
                                                    href="http://movie.douban.com/subject/5262275/"><font color="green">豆瓣</font></a><span>9.2</span><br/><a
                                        target="_blank" href="https://www.imdb.com/title/tt0460649/"><font
                                        color="#E0C035">IMDb</font>8.3</a></div>
                            </td>
                            <td class="embedded"><a
                                    href="https://www.pttime.org/download.php?id=72796&amp;passkey=ed4a5dad64710ab6c22de7357e5b4505&amp;uid=64181">📥</a><br/><a
                                    id="bookmark36" href="javascript:%20bookmark(72796,36);">🤍</a><a id="myrss36"
                                                                                                     href="javascript:%20myrss(72796,36);">🏁</a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </td>
    <td class="rowfollow dn" style="display:none">0</td>
    <td class="rowfollow"><b><a
            href="https://www.pttime.org/details.php?id=72796&amp;hit=1&amp;cmtpage=1#startcomments">0</a></b></td>
    <td class="rowfollow nowrap"><span title="2024-05-10 09:54:03">6时<br/>44分</span></td>
    <td class="rowfollow">16.21<br/>GB</td>
    <td class="rowfollow" align="center"><b><a
            href="https://www.pttime.org/details.php?id=72796&amp;hit=1&amp;dllist=1#seeders"><font
            color="#ff0000">1</font></a></b></td>
    <td class="rowfollow"><b><a
            href="https://www.pttime.org/details.php?id=72796&amp;hit=1&amp;dllist=1#leechers">133</a></b></td>
    <td class="rowfollow">0</td>
    <td class="rowfollow">-</td>
    <td class="rowfollow"><i>匿名</i></td>
    <td class="rowfollow"/>
</tr>

"""







def filter_text(text, filters):
    """
    对文件进行处理
    """
    if not text or not filters or not isinstance(filters, list):
        return text
    if not isinstance(text, str):
        text = str(text)
    for filter_item in filters:
        try:
            method_name = filter_item.get("name")
            args = filter_item.get("args")
            if method_name == "re_search" and isinstance(args, list):
                text = re.search(r"%s" % args[0], text).group(args[-1])
            elif method_name == "split" and isinstance(args, list):
                text = text.split(r"%s" % args[0])[args[-1]]
            elif method_name == "replace" and isinstance(args, list):
                text = text.replace(r"%s" % args[0], r"%s" % args[-1])
            elif method_name == "dateparse" and isinstance(args, str):
                text = datetime.datetime.strptime(text, r"%s" % args)
            elif method_name == "strip":
                text = text.strip()
            elif method_name == "appendleft":
                text = f"{args}{text}"
        except Exception as err:
            ExceptionUtils.exception_traceback(err)
    return text.strip()

filters = [
    {
        "name": "re_search",
        "args": [
            "\\d+-\\d+-\\d+ \\d+:\\d+:\\d+",
            0
        ]
    },
    {
        "name": "dateparse",
        "args": "%Y-%m-%d %H:%M:%S"
    }
]

torrent = PyQuery(html)
p = torrent('td:nth-child(2) > table > tr > td.embedded > span[title]')
items = [item.attr('title') for item in p.items() if item]
item = items[0] if items else ''
text = filter_text(item, filters)
print(text)


import datetime
now = datetime.datetime.now()

stripped_str_now = now.strftime('%Y-%m-%d %H:%M:%S').strip()
print(stripped_str_now)