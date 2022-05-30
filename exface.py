from PIL import Image, ImageDraw
import requests
from io import BytesIO


def expand(image, size):
    w, h = image.size
    bg = Image.new('RGBA', (int(size*w), int(size*h)), (0, 0, 0, 0))
    bg.paste(image, (int((size-1)/2*w), int((size-1)/2*h)))
    return bg


def exface(face, pendant):
    # 头像
    if isinstance(face, str):
        response = requests.get(face)  # 请求图片
        face = Image.open(BytesIO(response.content))  # 读取图片
    w, h = face.size

    a = Image.new('L', face.size, 0)  # 创建一个黑色背景的画布
    ImageDraw.Draw(a).ellipse((0, 0, a.width, a.height), fill=255)  # 画白色圆形

    # 粉圈
    if not pendant:
        image = Image.new('RGBA', (int(1.16*w), int(1.16*h)), (0, 0, 0, 0))
        image.paste(face, (int(0.08*w), int(0.08*h)), mask=a)  # 粘贴至背景
        ps = Image.new("RGB", (int(1.16*w), int(1.16*h)), (242, 93, 142))
        a = Image.new('L', ps.size, 0)  # 创建一个黑色背景的画布
        ImageDraw.Draw(a).ellipse((0, 0, a.width, a.height), fill=255)  # 画白色外圆
        ImageDraw.Draw(a).ellipse((int(0.06*w), int(0.06*h), int(1.1*w), int(1.1*h)), fill=0)  # 画黑色内圆
        image.paste(ps, (0, 0), mask=a)  # 粘贴至背景
        image = expand(image, 1.25)
    # 装扮
    else:
        image = Image.new('RGBA', (int(1.75*w), int(1.75*h)), (0, 0, 0, 0))
        image.paste(face, (int(0.375*w), int(0.375*h)), mask=a)  # 粘贴至背景
        response = requests.get(pendant)  # 请求图片
        pd = Image.open(BytesIO(response.content))  # 读取图片
        pd = pd.resize((int(1.75*w), int(1.75*h)), Image.ANTIALIAS)  # 装扮应当是头像的1.75倍
        r, g, b, a = pd.split()  # 分离alpha通道
        image.paste(pd, (0, 0), mask=a)  # 粘贴至背景
    
    return image


if __name__ == '__main__':
    face = Image.open('./images/0.png')
    image = exface(face, None)
