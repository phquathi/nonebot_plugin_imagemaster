import cv2
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os

current_directory = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(current_directory, 'songti.ttf')


def apply_filter(image_data, filter_type):
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
        noise = np.random.randint(0, 5, img.shape, dtype='uint8')
        img_noisy = cv2.add(img_float, noise.astype(np.float32))
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
        img = apply_mosaic(img, 0, 0, img.shape[1], img.shape[0], 10)
    elif filter_type == "前景提取":
        img = extract_foreground(img)

    _, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes()


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
    return buffer.tobytes()


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


def stitch_images(image_list):
    decoded_images = [cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR) for img_data in image_list]

    widths, heights = zip(*(img.shape[1::-1] for img in decoded_images))

    images_per_row = 3
    num_rows = (len(decoded_images) + images_per_row - 1) // images_per_row

    max_width_per_row = sum(sorted(widths, reverse=True)[:images_per_row])
    max_height_per_image = max(heights)
    total_width = max_width_per_row
    total_height = max_height_per_image * num_rows

    stitched_image = np.zeros((total_height, total_width, 3), dtype=np.uint8)
    stitched_image.fill(255)

    current_x = 0
    current_y = 0
    for i, img in enumerate(decoded_images):
        h, w = img.shape[:2]
        if i % images_per_row == 0 and i != 0:
            current_y += max_height_per_image
            current_x = 0
        stitched_image[current_y:current_y + h, current_x:current_x + w] = img
        current_x += w

    _, buffer = cv2.imencode('.jpg', stitched_image)
    return buffer.tobytes()


def add_text_to_image(image_data, text):
    img = Image.open(BytesIO(image_data))

    # 计算合适字体大小
    img_width, img_height = img.size
    font_size = img_width // len(text)
    font_size = max(min(font_size, 120), 20)

    font = ImageFont.truetype(font_path, font_size)

    draw = ImageDraw.Draw(img)

    # 阴影效果
    shadowcolor = "black"

    # 文字居中
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    x = (img_width - text_width) / 2
    y = (img_height - text_height) / 2 + img_height // 4

    # 文字阴影
    draw.text((x-1, y-1), text, font=font, fill=shadowcolor)
    draw.text((x+1, y-1), text, font=font, fill=shadowcolor)
    draw.text((x-1, y+1), text, font=font, fill=shadowcolor)
    draw.text((x+1, y+1), text, font=font, fill=shadowcolor)

    draw.text((x, y), text, font=font, fill="white")

    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    _, buffer = cv2.imencode('.jpg', img_cv)
    return buffer.tobytes()
