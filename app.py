import asyncio
import os
from logging import DEBUG, Formatter, Logger, StreamHandler

import aiohttp
from pywebio import config, start_server
from pywebio.input import *
from pywebio.io_ctrl import Output
from pywebio.output import *
from pywebio.session import eval_js, go_app
from pywebio.session import info as sif
from pywebio.session import local, run_async
from pywebio.session import run_asyncio_coroutine as rac
from pywebio.session import run_js

config(js_code='''$("body").prepend('<nav class="navbar navbar-dark bg-dark"><div class="container"><a href="/?app=code" class="router-link-active router-link-exact-active navbar-brand">😎</a><a href="/"><img src="https://s1.ax1x.com/2022/07/11/jyaevn.png" height="40px"></a><a href="/?app=admin" class="router-link-active router-link-exact-active navbar-brand">🛒</a></div></nav>')''')

import account
import exface
from bili import BILI
from linkedlist import LinkedList
from config import get_configs, loads, dumps
from database import userDB, configDB

logger = Logger('MAIN', DEBUG)
handler = StreamHandler()
handler.setFormatter(Formatter("`%(asctime)s` %(message)s", '%H:%M:%S'))
logger.addHandler(handler)
LOGIN_COUNT = {}
Headers = {
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
}
SESSION = aiohttp.ClientSession(headers=Headers)
loglist = LinkedList(20, (-1, 'Hello LinkedList'))


async def get_config(username: str):
    config = userDB.query('CONFIG', USERNAME=username)
    if not config or config == 'None':
        config = ''
    resp = await eval_js(f'prompt("编辑配置，以英文半角逗号(,)分隔", "{config}");')
    saved = []
    try:
        for cid in resp.split(','):
            if cid.isdigit() and cid not in saved:
                saved.append(cid)
        assert resp == '' or len(saved) != 0, '配置错误'
        userDB.update(username, CONFIG=','.join(saved))
    except Exception as e:
        toast('配置错误', 3, color='error')
        logger.error(e)
    run_js('location.reload();')


async def new_config(username: str):
    config = userDB.query('CONFIG', USERNAME=username).split(',')
    next_cid = str(configDB.get_last_cid() + 1)
    ans = await select('请选择添加配置方式', ['自动导入 配置文件', '手动填写 配置文件', '填写 json 配置文件', '上传 json 配置文件'])
    match ans:
        case '自动导入 配置文件':
            cid = str(await input('请输入配置文件编号', NUMBER, required=True))
            if cid not in config:
                userDB.update(username, CONFIG=','.join(config+[cid]))
            run_js('location.reload();')
        case '手动填写 配置文件':
            put_markdown('#### 摆了没做嘻嘻')
        case '填写 json 配置文件':
            inputs = await input_group(
                label='填写配置文件',
                inputs=[
                    input("给你的配置取个名", type=TEXT, required=True, name='name'),
                    textarea('config.json', rows=10, code=True, name='cont')
                ]
            )
            try:
                new_config = dumps(loads(inputs['cont']), indent=4, ensure_ascii=False)
                configDB.insert(CID=next_cid, NAME=inputs['name'], OWNER=username, DATA=new_config)
                userDB.update(username, CONFIG=','.join(config+[next_cid]))
                run_js('location.reload();')
            except Exception as e:
                toast(f'配置文件错误：{e}', 3, color='error')
        case '上传 json 配置文件':
            file = await file_upload('上传配置文件，将以文件名作为展示配置名', accept=['.json', '.txt'],max_size='5K', required=True, help_text='请上传不大于 5Kb 以 .json 或 .txt 后缀的文件')
            try:
                new_config = dumps(loads(file['content']), indent=4, ensure_ascii=False)
                configDB.insert(CID=next_cid, NAME=os.path.splitext(file['filename'])[0], OWNER=username, DATA=new_config)
                userDB.update(username, CONFIG=','.join(config+[next_cid]))
                run_js('location.reload();')
            except Exception as e:
                toast(f'配置文件错误：{e}', 3, color='error')


async def location(ipv6: str):
    if not ipv6:
        return
    BASEURL = 'http://ip.zxinc.org/api.php?type=json'
    r = await rac(SESSION.get(BASEURL, params={'ip': ipv6}))
    return (await rac(r.json(content_type='text/json')))['data']['location'].replace('\t', ' ')


async def bind():
    '绑定账号'
    username = await account.get()
    bili = local.bili
    bili: BILI()

    if bili:
        def on_click(btn):
            if btn == '后台':
                if username == 'Admin':
                    go_app('admin', False)
                else:
                    toast('权限不足', 5, color='error')
            elif btn == '编辑配置':
                run_async(get_config(username))
            else:
                if btn == '退出':
                    account.clear()
                run_js('location.reload();')

        keys = ['USERNAME', 'PASSWORD', 'UID', 'NICKNAME', 'FACE', 'PENDANT', 'COLOR', 'SESSDATA', 'BILI_JCT', 'BUVID3', 'CONFIG', 'IP']
        values = list(userDB.query(USERNAME=username))
        values[1] = '*' * len(values[1])
        items = list(zip(keys, values))

        popup('已绑定信息', [
            put_table([['Key', 'Value']] + [list(item) for item in items] + [['LOCATION', await location(values[-1])]]),
            put_buttons(['确定', '后台', '编辑配置', {'label': '退出登录', 'color': 'danger', 'value': '退出'}], onclick=on_click),
        ], size='large')
    
    if not bili:
        if bili.running:
            return

        logger.debug('模拟登录')

        task = run_async(bili.login())

        while not task.closed():
            logger.debug('轮询中')
            await asyncio.sleep(3)
        else:
            logger.debug('轮询结束')

    if not bili:
        return

    logger.debug(f'绑定成功, uid={bili.uid}')

    info = await rac(bili.get_info())
    logger.debug(f'信息更新成功')

    userDB.update(username, 
        UID=bili.uid,
        NICKNAME=info.get('name'),
        FACE=info.get('face'),
        PENDANT=info.get('pendant', {}).get('image'),
        COLOR=info.get('vip', {}).get('nickname_color', '#000000'),
        **bili.cookies
    )

    image = await exface.exface(SESSION, info.get('face'), info.get('pendant', {}).get('image'))
    image.save(f'images/{bili.uid}.png')

async def index():
    '全托管独轮车'
    ip = sif.user_ip.replace('::1', '127.0.0.1')
    logger.debug(f'收到请求, ip={ip}')
    username = await account.get()
    
    if not username:
        def check_account(inputs):
            uid = inputs['uid']
            for char in uid:
                if not ('0' <= char <= '9' or 'a' <= char <= 'z' or 'A' <= char <= 'Z'):
                    return ('uid', '仅支持字母与数字组合')
            cnt = LOGIN_COUNT.get(uid, 0) + 1
            LOGIN_COUNT[uid] = cnt
            if cnt > 10:
                return ('uid', '别试了，账户给你锁了')
            elif cnt > 5:
                toast('赫赫，想暴力破密码是吧', color='error')
            
            inputs['code'] = userDB.query('PASSWORD', USERNAME=inputs['uid'])
            logger.debug('输入完成, username={uid}, password={pwd}, code={code}'.format_map(inputs))

            if inputs['code'] and not inputs['code'] == inputs['pwd']:
                return ('pwd', '密码错误')
            LOGIN_COUNT[uid] = 0

        while True:
            inputs = await input_group(
                label='登录/注册账号',
                inputs=[
                    input("用户名", type=TEXT, placeholder='唯一且不可修改', required=True, name='uid'),
                    input("密码", type=PASSWORD, placeholder='MD5加密保存', help_text='译验丁真，鉴定为：我猜你密码', required=True, name='pwd'),
                    actions(name='cmd', buttons=['登录/注册'])
                ],
                validate=check_account
            )
            
            if not inputs['code']:
                userDB.insert(USERNAME=inputs['uid'], PASSWORD=inputs['pwd'], IP=ip)
                toast('注册成功！重新填写账户信息以登录！', duration=5)
            else:
                username = inputs['uid']
                break

    account.save(username)
    userDB.update(username, IP=ip)
    await main(username, ip)


async def refresh_msg(loglist: LinkedList, scope=None):
    sleeptime = 1
    local.loglist = loglist
    node = loglist.getTrueHead()
    while True:
        await asyncio.sleep(sleeptime)
        while node.getNext():
            try:
                node = node.getNext()
                if scope:
                    msg = node.getValue()
                    put_markdown(msg, sanitize=True, scope=scope)
                else:
                    cid, msg = node.getValue()
                    if '/ s`' in msg:
                        clear(f'scrollable_{cid}_hb')
                        put_markdown(msg, sanitize=True, scope=f'scrollable_{cid}_hb').style('border-bottom: none')
                    else:
                        put_markdown(msg, sanitize=True, scope=f'scrollable_{cid}')
            except Exception as e:
                print('error', msg)
                toast(f'msg error: {e}', 3, color='error')

    
async def main(username: str, ip: str):
    uid, name, color, face, pendant = userDB.query('UID,NICKNAME,COLOR,FACE,PENDANT', USERNAME=username)
    try:
        with open(f'images/{uid}.png', 'rb') as fp:
            face = fp.read()
    except Exception as e:
        logger.error(f'加载头像错误: {e}')
        face = await exface.exface(SESSION, face, pendant)
        face.save(f'images/{uid}.png')

    uid, config, *cookies = userDB.query(cmd='UID,CONFIG,SESSDATA,BILI_JCT,BUVID3', USERNAME=username)
    local.bili = BILI(uid, cookies)

    while await rac(local.bili.check()) in [-400, -101, -111]:
        await bind()

    put_column([
        put_row([
            put_image(face, format='png', height='100px').onclick(bind),
            put_column([
                None,
                put_html(f'<b><font color="{color}" size="5px">&nbsp;{name}</font><font color="grey" size="3px">&nbsp;&nbsp;IP属地: {await location(ip)}</font></b>'),
            ], size='auto'),
            None
        ], size='auto 1fr auto'),
        None
    ] + get_configs(username, config), size='7fr 1fr auto')

    put_button('添加配置', onclick=lambda: new_config(username))
    
    run_async(refresh_msg(loglist))


async def admin():
    '后台'
    username = await account.get()
    if not username == 'Admin':
        put_markdown('# `Admin权限不足`')
        return
    put_scrollable(put_scope('admin_scrollable'), height=400, keep_bottom=True)
    while True:
        cmd = await input('Command')
        put_markdown(f'`>>>` {cmd}', scope='admin_scrollable')
        logger.info(cmd)
        if cmd == 'exit()':
            break
        try:
            value = eval(cmd)
            if not isinstance(value, Output):
                put_markdown(f'`Server` {value}', scope='admin_scrollable')
        except Exception as e:
            logger.error(e)
            toast(e, 5)
    go_app('index', False)


def code():
    widgets = [put_markdown('# 😎你知道我长什么样 来找我吧')]
    for root, folders, files in os.walk('.'):
        for file in files:
            if file.split('.')[-1] == 'py':
                with open(file, 'r', encoding='utf-8') as fp:
                    code_str = fp.read()
                    widgets.append(put_collapse(file, put_code(code_str, 'python')))
        break
    put_tabs([
        {'title': '每日必听', 'content': put_html('''
                <iframe src="//player.bilibili.com/player.html?aid=78090377&bvid=BV1vJ411B7ng&cid=133606284&page=1"
                    width="100%" height="550" scrolling="true" border="0" frameborder="no" framespacing="0" allowfullscreen="true">
                </iframe>''')},
        {'title': '网页源码', 'content': widgets}
    ]).style('border:none;')


if __name__ == '__main__':
    start_server([index, admin, code], port=2434, auto_open_webbrowser=True, debug=True)
