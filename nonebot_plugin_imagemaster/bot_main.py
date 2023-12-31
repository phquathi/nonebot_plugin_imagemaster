import os

import httpx
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Bot, Event
from nonebot.typing import T_State
from nonebot.rule import to_me

from .image_editor import apply_filter, crop_image, stitch_images, add_text_to_image

current_directory = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_directory, '图片1.png')

# 图像处理功能
image_process = on_command("图片处理", rule=to_me(), priority=2)


@image_process.got("image", prompt="请发送图片")
async def handle_image(bot: Bot, event: Event, state: T_State):
    message = event.get_message()
    for msg_segment in message:
        if msg_segment.type == "image":
            image_url = msg_segment.data['url']
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                state["image_data"] = response.content
            await image_process.send(MessageSegment.image(f"file:///{image_path}"))
            return
    await image_process.reject("未检测到图片，请重新发送图片")


@image_process.got("command", prompt="请根据指令表选择处理方式")
async def handle_command(bot: Bot, event: Event, state: T_State):
    command_text = state["command"].extract_plain_text().strip().lower()
    image_data = state["image_data"]
    try:
        processed_image = apply_filter(image_data, command_text)
        await image_process.send(processed_image)
        await image_process.send("图片处理完成。")
    except Exception as e:
        await image_process.finish(f"处理图片时出现错误: {str(e)}")


# 图像裁剪功能
image_crop = on_command("图像裁剪", rule=to_me(), priority=2)


@image_crop.got("image", prompt="请发送图片")
async def handle_image_crop(bot: Bot, event: Event, state: T_State):
    message = event.get_message()
    for msg_segment in message:
        if msg_segment.type == "image":
            image_url = msg_segment.data['url']
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                state["image_data"] = response.content
            return
    await image_crop.reject("未检测到图片，请重新发送图片")


@image_crop.got("command", prompt="请发送要保留的部分（上、下、左、右）")
async def handle_command_crop(bot: Bot, event: Event, state: T_State):
    command_text = state["command"].extract_plain_text().strip().lower()
    image_data = state["image_data"]

    try:
        processed_image = crop_image(image_data, command_text)
        await image_crop.send(processed_image)
        await image_crop.send("图片裁剪完成。")
    except Exception as e:
        await image_crop.finish(f"裁剪图片时出现错误: {str(e)}")


# 图像拼接功能
image_stitch = on_command("图像拼接", rule=to_me(), priority=2)


@image_stitch.got("image_count", prompt="请发送需要拼接的图片数量")
async def handle_image_count(bot: Bot, event: Event, state: T_State):
    image_count = state["image_count"].extract_plain_text().strip()
    if not image_count.isdigit():
        await image_stitch.reject("您输入的不是有效的数字，请重新发送图片数量")
    else:
        state["image_count"] = int(image_count)
        await image_stitch.send(f"请一次性发送{state['image_count']}张图片")


@image_stitch.got("image")
async def handle_image_stitch(bot: Bot, event: Event, state: T_State):
    images = []

    if "停止拼接" in str(event.get_message()):
        await image_stitch.finish("图像拼接已停止。")
        return

    message = event.get_message()
    for msg_segment in message:
        if msg_segment.type == "image":
            image_url = msg_segment.data['url']
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                images.append(response.content)

    if len(images) < state["image_count"]:
        await image_stitch.reject(f"未收到足够数量的图片，请一次性发送{state['image_count']}张图片")

    try:
        stitched_image = stitch_images(images)
        await image_stitch.send(stitched_image)
    except Exception as e:
        await image_stitch.finish(f"拼接图片时出现错误: {str(e)}")


# 表情包制作
meme_maker = on_command("表情包制作", rule=to_me(), priority=2)


@meme_maker.got("image", prompt="请发送要制作表情包的图片")
async def handle_image(bot: Bot, event: Event, state: T_State):
    message = event.get_message()
    for msg_segment in message:
        if msg_segment.type == "image":
            image_url = msg_segment.data['url']
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                state["image_data"] = response.content
            await meme_maker.send("请发送要添加的文字")
            return
    await meme_maker.reject("未检测到图片，请重新发送图片")


@meme_maker.got("text")
async def handle_text(bot: Bot, event: Event, state: T_State):
    text_to_add = str(state["text"]).strip()
    if not text_to_add:
        await meme_maker.reject("文字不能为空，请重新发送")
    try:
        meme_image = add_text_to_image(state["image_data"], text_to_add)
        await meme_maker.send(meme_image)
    except Exception as e:
        await meme_maker.finish(f"制作表情包时出现错误: {str(e)}")

# 文字识别
# text_extraction = on_command("文字提取", rule=to_me(), priority=2)
#
#
# @text_extraction.handle()
# async def handle_first_receive_ocr(bot: Bot, event: Event, state: T_State):
#     await text_extraction.send("请发送图片")
#
#
# @text_extraction.got("image", prompt="请发送图片")
# async def handle_image_ocr(bot: Bot, event: Event, state: T_State):
#     message = event.get_message()
#
#     for msg_segment in message:
#         if msg_segment.type == "image":
#             image_url = msg_segment.data['url']
#             image_data = requests.get(image_url).content
#
#
#             with ThreadPoolExecutor() as pool:
#                 try:
#
#                     extracted_text = await asyncio.get_event_loop().run_in_executor(
#                         executor, lambda: extract_text(image_data)
#                     )
#                     await text_extraction.finish(f"提取的文字内容是：\n{extracted_text}")
#                 except Exception as e:
#                     await text_extraction.finish(f"处理图片时出现错误: {str(e)}")
#                     return
#
#     await text_extraction.reject("未检测到图片，请重新发送图片")
