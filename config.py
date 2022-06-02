from pywebio.output import *
from pywebio.session import run_async
from database import userDB, configDB
from night import night
from json import loads
from bilibili_api import Credential
from functools import partial
from linkedlist import LinkedList
from WebHandler import WebHandler
from logging import INFO, Formatter, Logger


loglist = LinkedList(20, (0, 'loglist启动中'))

logger = Logger('TASK', INFO)
handler = WebHandler(loglist=loglist, dot=True)
handler.setFormatter(Formatter("`%(asctime)s` `%(levelname)s` `Task`: %(message)s", '%Y-%m-%d %H:%M:%S'))
logger.addHandler(handler)

tasks = {}


async def on_click(btn: str, data):
    username, cid, code = btn.split('.')
    if not tasks.get(username):
        cookies = userDB.query('SESSDATA,BILI_JCT,BUVID3', USERNAME=username)
        credential = Credential(*cookies)
        tasks[username] = {'credential': credential}
    # put_markdown(f'`{btn}`', scope=f'scrollable_{cid}')
    if code == 'run':
        task = tasks.get(username, {}).get(cid)
        if not task:
            tasks[username][cid] = night(cid, logger, tasks[username]['credential'], data)
    elif code == 'close':
        task = tasks.get(username, {}).get(cid)
        if task:
            await task.close()
            del tasks[username][cid]


def get_configs(username, cids):
    configs = configDB.query(cids)
    widgets = []
    for cid, name, owner, data in configs:
        js = loads(data)
        color, bname = userDB.query('COLOR,NICKNAME', USERNAME=owner)
        widgets.append(
            put_collapse(f'配置：{name}', [
                put_tabs([
                    {'title': '基本信息', 'content': [
                        put_markdown(f'`配置所有`：<font color="{color}">{bname}</font>'),
                        put_markdown(f'`配置序号`：{cid}'),
                        put_markdown(f'`直播间号`：{js["roomid"]}'),
                        put_markdown(f'`监听阈值`：{js["limited_density"]}'),
                        put_markdown(f'`输出间隔`：{js["send_rate"]}'),
                        put_markdown('`监听词句`：\n&emsp;'+"\n&emsp;".join(js["listening_words"])),
                        put_markdown('`输出词句`：\n&emsp;'+"\n&emsp;".join(js["goodnight_words"])),
                    ]},
                    {
                        'title': '输出终端',
                        'content': [
                            put_buttons([
                                {'label': '▷', 'value': f'{username}.{cid}.run'},
                                {'label': '■', 'color': 'danger', 'value': f'{username}.{cid}.close'}
                            ], onclick=partial(on_click, data=js)),
                            put_scrollable(put_scope(f'scrollable_{cid}'), height=200, keep_bottom=True)
                        ]
                    },
                    {'title': '源代码', 'content': put_code(data, 'json')},
                ]).style('border:none;')
            ])
        )
    return widgets


if __name__ == '__main__':
    '''
    configDB.insert(CID=1, NAME='曹你', OWNER='Admin', DATA='fuck you')
    configDB.insert(CID=2, NAME='曹我', OWNER='Admin2', DATA='fuck me')
    configDB.insert(CID=3, NAME='曹谁', OWNER='Admin3', DATA='fuck who')
    '''
