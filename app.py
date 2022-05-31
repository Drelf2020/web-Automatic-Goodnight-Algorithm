import asyncio
from logging import DEBUG, Formatter, Logger

import requests
from pywebio import start_server
from pywebio.input import *
from pywebio.io_ctrl import Output
from pywebio.output import *
from pywebio.session import go_app, eval_js, run_js
from pywebio.session import info as sif
from pywebio.session import local, run_async
from pywebio.session import run_asyncio_coroutine as rac

import exface
from linkedlist import LinkedList
from WebHandler import WebHandler

loglist = LinkedList(20)

logger = Logger('MAIN', DEBUG)
handler = WebHandler(loglist=loglist)
handler.setFormatter(Formatter("`%(asctime)s` `%(levelname)s` `Main`: %(message)s", '%Y-%m-%d %H:%M:%S'))
logger.addHandler(handler)

import account
from bili import BILI
from config import get_configs
from database import userDB

LOGIN_COUNT = {}
 

async def get_config(username):
    config = userDB.query('CONFIG', USERNAME=username)
    if not config or config == 'None':
        config = ''
    resp = await eval_js(f'prompt("编辑配置，以英文半角逗号(,)分隔", "{config}");')
    saved = []
    if resp:
        try:
            for cid in resp.split(','):
                if cid.isdigit() and cid not in saved:
                    saved.append(cid)
            userDB.update(username, CONFIG=','.join(saved))
        except Exception as e:
            toast('配置错误', 3, color='error')
            logger.error(e)
    run_js('location.reload();')


async def bind():
    '绑定账号'
    username = await account.get()
    bili = local.bili
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

        def location(ipv6: str):
            if not ipv6:
                return
            BASEURL = 'http://ip.zxinc.org/api.php?type=json'
            r = requests.get(BASEURL, params={'ip': ipv6})
            return r.json()['data']['location'].replace('\t', ' ')

        popup('已绑定信息', [
            put_table([['Key', 'Value']] + [list(item) for item in items] + [['LOCATION', location(values[-1])]]),
            put_buttons(['确定', '后台', '编辑配置', {'label': '退出登录', 'color': 'danger', 'value': '退出'}], onclick=on_click),
        ], size='large')

        logger.debug(f'检查绑定, uid={bili.uid}')
        code = await rac(bili.check())
        if code in [-400, -101, -111]:
            bili.uid = None
        logger.debug(f'账号状态, code={code}')
    
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

    image = exface.exface(info.get('face'), info.get('pendant', {}).get('image'))
    image.save(f'images/{bili.uid}.png')


async def index():
    '全托管独轮车'
    ip = sif.user_ip.replace('::1', '127.0.0.1')
    logger.debug(f'收到请求, ip={ip}')
    username = await account.get()

    if not username:
        def check_account(inputs):
            uid = inputs['uid']
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
                    input("用户名", type=TEXT, placeholder='唯一但可修改', required=True, name='uid'),
                    input("密码", type=PASSWORD, placeholder='加密保存', help_text='真的', required=True, name='pwd'),
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
    await main()

    
async def main():
    username = await account.get()
    uid, name, color, face, pendant = userDB.query('UID,NICKNAME,COLOR,FACE,PENDANT', USERNAME=username)
    try:
        with open(f'images/{uid}.png', 'rb') as fp:
            face = fp.read()
    except Exception as e:
        logger.error(f'加载头像错误: {e}')
        face = exface.exface(face, pendant)
        face.save(f'images/{uid}.png')
    
    if not name:
        name = username + '，请点击头像绑定账号'

    uid, config, *cookies = userDB.query(cmd='UID,CONFIG,SESSDATA,BILI_JCT,BUVID3', USERNAME=username)
    local.bili = BILI(uid, cookies)

    put_column([
        put_row([
            put_image(face, format='png', height='100px').onclick(bind),
            put_column([
                None,
                put_markdown(f'## 😚欢迎你呀，<font color="{color}">{name}🥳</font>').style('border-bottom: none'),
                None
            ]),
            None
        ], size='auto auto 1fr'),  # .style('border-style: solid;'),
        put_markdown('---')
    ] + get_configs(username, config), size='auto auto 1fr')


async def refresh_msg():
    global loglist
    count = 0
    sleeptime = 0.5
    node = loglist.getTrueHead()
    while True:
        count += 1
        if count >= 10/sleeptime:
            logger.debug('Heartbeat')
            count = 0
        await asyncio.sleep(sleeptime)
        while node.getNext():
            node = node.getNext()
            m = node.getValue()
            put_markdown(m, sanitize=True, scope='admin_scrollable')

async def admin():
    username = await account.get()
    if not username == 'Admin':
        put_markdown('`Admin权限不足`')
        return
    put_scrollable(put_scope('admin_scrollable'), height=400, keep_bottom=True)
    task = run_async(refresh_msg())
    while True:
        cmd = await input('Command')
        logger.info(cmd)
        if cmd == 'exit()':
            break
        try:
            value = eval(cmd)
            if not isinstance(value, Output):
                toast(value, 5)
        except Exception as e:
            logger.error(e)
            toast(e, 5)
    task.close()
    run_js('location.reload();')


if __name__ == '__main__':
    start_server([index, admin], port=2434, auto_open_webbrowser=True, debug=True)
