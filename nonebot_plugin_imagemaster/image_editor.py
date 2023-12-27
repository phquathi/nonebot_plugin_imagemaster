import cv2
import numpy as np
from io import BytesIO
from nonebot.adapters.onebot.v11 import MessageSegment


def apply_filter(image_data, filter_type):
    """
    :param image_data: 接收到的图像数据。
    :param filter_type: 要应用的滤镜类型。
    """
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if filter_type == "黑白":
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif filter_type == "提高对比度":
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    elif filter_type == "模糊":
        img = cv2.GaussianBlur(img, (5, 5), 0)
    elif filter_type == "边缘显示":
        img = cv2.Canny(img, 100, 200)
    elif filter_type == "浮雕":
        kernel = np.array([[0, -1, -1],
                           [1, 0, -1],
                           [1, 1, 0]])
        img = cv2.filter2D(img, -1, kernel)
    elif filter_type == "鲜明":
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = cv2.add(hsv[:, :, 1], 15)  # 增加饱和度
        img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    elif filter_type == "负片":
        img = cv2.bitwise_not(img)
    elif filter_type == "胶片颗粒":
        img_float = img.astype(np.float32)
        # 生成噪声
        noise = np.random.randint(0, 5, img.shape, dtype='uint8')
        img_noisy = cv2.add(img_float, noise.astype(np.float32))
        # 换回uint8
        img = np.clip(img_noisy, 0, 255).astype(np.uint8)
    elif filter_type in ["微红", "暖橙", "柔黄", "奶绿", "微蓝", "清靛", "幽紫"]:
        tints = {
            "微红": [1.15, 1, 1],
            "暖橙": [1.15, 1.07, 1],
            "柔黄": [1, 1.15, 1],
            "奶绿": [1, 1.15, 1.07],
            "微蓝": [1, 1, 1.15],
            "清靛": [1.07, 1, 1.15],
            "幽紫": [1.15, 1, 1.07]
        }
        img = tint_image(img, tints[filter_type])
    elif filter_type == "马赛克":
        # 对整个图像应用马赛克
        img = apply_mosaic(img, 0, 0, img.shape[1], img.shape[0], 10)
    elif filter_type == "前景提取":
        img = extract_foreground(img)

    _, buffer = cv2.imencode('.jpg', img)
    img_bytes = BytesIO(buffer)
    return MessageSegment.image(img_bytes)


def crop_image(image_data, direction):
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    h, w = img.shape[:2]

    if direction == "上":
        img = img[:h // 2, :]
    elif direction == "下":
        img = img[h // 2:, :]
    elif direction == "左":
        img = img[:, :w // 2]
    elif direction == "右":
        img = img[:, w // 2:]

    _, buffer = cv2.imencode('.jpg', img)
    img_bytes = BytesIO(buffer)
    return MessageSegment.image(img_bytes)


def apply_mosaic(img, x, y, width, height, mosaic_size):
    img[y:y + height, x:x + width] = cv2.resize(
        cv2.resize(img[y:y + height, x:x + width], (mosaic_size, mosaic_size)),
        (width, height), interpolation=cv2.INTER_AREA)
    return img


def extract_foreground(image):
    mask = np.zeros(image.shape[:2], np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    rect = (50, 50, 400, 500)

    cv2.grabCut(image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

    mask = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
    foreground = image * mask[:, :, np.newaxis]

    return foreground


def tint_image(img, tint):

    tint_array = np.array(tint, dtype=np.float32).reshape(1, 1, 3)

    img_float = img.astype(np.float32)

    img_tinted = cv2.multiply(img_float, tint_array)

    img_tinted = np.clip(img_tinted, 0, 255).astype(np.uint8)

    return img_tinted
