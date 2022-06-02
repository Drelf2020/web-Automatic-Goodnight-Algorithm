from bilibili_api.live import LiveDanmaku, LiveRoom, Danmaku
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pywebio.output import *
from pywebio.session import run_asyncio_coroutine as rac, run_async
import re


class night:

    def __init__(self, cid, logger, credential, data):
        run_async(self.run(cid, logger, credential, data))

    async def close(self):
        self.sched.shutdown()
        await rac(self.listen_room.disconnect())

    async def run(self, cid, logger, credential, data):
        '全自动晚安机'
        logger.info(f'配置: {cid} 正在启动.{cid}')
    
        self.listen_room = LiveDanmaku(int(data['roomid']))  # 接收弹幕, debug=True
        send_room = LiveRoom(int(data['roomid']), credential)  # 发送弹幕
        self.sched = AsyncIOScheduler()  # 定时检测密度的任务调度器

        danmuku_list = []  # 储存一段时间晚安弹幕
        count_danmuku = 0  # 储存某时间点晚安弹幕
        total_danmuku = 0  # 统计一段时间总晚安弹幕
        last_time = 0  # 上一次储存弹幕时的时间戳

        regex = '(' + ')|('.join(data['listening_words']) + ')'
        regex = re.compile(regex)  # 正则监听词
        density = data['limited_density']

        goodnight = data['goodnight_words']  # 发送弹幕库
        send_count = 0  # 发送计数器

        @self.listen_room.on('DANMU_MSG')
        async def on_danmaku(event):
            '接收弹幕并计算密度'
            nonlocal danmuku_list, count_danmuku, total_danmuku, last_time
            info = event['data']['info']
            time = info[9]['ts']  # 时间戳
            if time > last_time:
                last_time = time
                danmuku_list.append(count_danmuku)  # 把上个时间戳记录的弹幕数储存并归零
                count_danmuku = 0
                total_danmuku += danmuku_list[-1]  # 总弹幕数增加
                if len(danmuku_list) > 5:  # 只记录最近 5 个时间戳内的弹幕 可改
                    total_danmuku -= danmuku_list.pop(0)  # 从总弹幕数总减去 删去了的时间戳内的弹幕数
            if regex.search(info[1]):
                count_danmuku += 1

        @self.sched.scheduled_job('interval', id='send_job', seconds=data['send_rate'])
        async def send_msg():
            '每 1 秒检测晚安弹幕密度 若超过阈值则随机发送晚安弹幕'
            nonlocal send_count
            logger.info('晚安弹幕密度：'+str(total_danmuku/5)+' / s'+f'.{cid}')
            if total_danmuku >= 5*density:  # 密度超过 5t/s 则发送晚安
                try:
                    word = goodnight[send_count % len(goodnight)]
                    send_count += 1
                    logger.info(f'发送晚安弹幕：{word}.{cid}')
                    await send_room.send_danmaku(Danmaku(word))
                except Exception as e:
                    logger.error(f'发送弹幕失败：{e}.{cid}')

        # 运行
        self.sched.start()
        await rac(self.listen_room.connect())