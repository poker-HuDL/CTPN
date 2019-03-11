import sys
import math
import copy
import cv2
import time
import os
import draw_image


# 从bbox生成anchor，把照片中的文本box转为小的条状anchor，ground truth
def generate_gt_anchor(img, box, anchor_width=16, draw_img_gt=None):
    """
    calsulate ground truth fine-scale box
    :param img: input image
    :param box: ground truth box (4 point)
    :param anchor_width:
    :return: tuple (position, h, cy)
    """
    if not isinstance(box[0], float):
        box = [float(box[i]) for i in range(len(box))]

    result = []
    # box数据格式为[x1 y1 x2 y2 x3 y3 x4 y4]，左上、右上、右下、左下
    left_anchor_num = int(math.floor(max(min(box[0], box[6]), 0) / anchor_width))  # the left side anchor of the text box, downwards
    right_anchor_num = int(math.ceil(min(max(box[2], box[4]), img.shape[1]) / anchor_width))  # the right side anchor of the text box, upwards

    # handle extreme case, the right side anchor may exceed the image width
    if right_anchor_num * 16 + 15 > img.shape[1]:
        right_anchor_num -= 1

    # combine the left-side and the right-side x_coordinate of a text anchor into one pair
    # 把一个box中的每个anchor左右边界以元组形式保存在position_pair中
    position_pair = [(i * anchor_width, (i + 1) * anchor_width - 1) for i in range(left_anchor_num, right_anchor_num)]

    # 计算每个gt anchor的真实位置，其实就是求解gt anchor的上边界和下边界
    y_top, y_bottom = cal_y_top_and_bottom(img, position_pair, box)

    #print("image shape: %s, pair_num: %s, top_num:%s, bot_num:%s" % (img.shape, len(position_pair), len(y_top), len(y_bottom)))

    # 最后将每个anchor的位置(水平ID，从左到右第几个anchor)、anchor中心y坐标、anchor高度存储并返回
    for i in range(len(position_pair)):
        position = int(position_pair[i][0] / anchor_width)  # the index of anchor box
        h = y_bottom[i] - y_top[i] + 1  # the height of anchor box
        cy = (float(y_bottom[i]) + float(y_top[i])) / 2.0  # the center point of anchor box
        result.append((position, cy, h))  # result保存图片中box的所有ground truth anchor的水平位置、y、h
        draw_img_gt = draw_image.draw_box_h_and_c(draw_img_gt, position, cy, h)  # 把anchor画出来
    draw_img_gt = draw_image.draw_box_4pt(draw_img_gt, box, color=(0, 0, 255), thickness=1)
    return result, draw_img_gt


# cal the gt anchor box's bottom and top coordinate
# 计算anchor的上下边界，可以用来计算anchor的高h、纵坐标中心cy
def cal_y_top_and_bottom(raw_img, position_pair, box):
    """
    :param raw_img:
    :param position_pair: for example:[(0, 15), (16, 31), ...]
    :param box: gt box (4 point)
    :return: top and bottom coordinates for y-axis
    """
    img = copy.deepcopy(raw_img)
    y_top = []
    y_bottom = []
    height = img.shape[0]
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            img[i, j, 0] = 0
    top_flag = False
    bottom_flag = False
    img = draw_image.draw_box_4pt(img, box, color=(255, 0, 0))
    # calc top y coordinate, pixel from top to down loop
    for k in range(len(position_pair)):
        # calc top y coordinate
        for y in range(0, height-1):
            # loop each anchor, from left to right
            for x in range(position_pair[k][0], position_pair[k][1] + 1):
                if img[y, x, 0] == 255:
                    y_top.append(y)
                    top_flag = True
                    break
            if top_flag is True:
                break
        # calc bottom y coordinate, pixel from down to top loop
        for y in range(height - 1, -1, -1):
            # loop each anchor, from left to right
            for x in range(position_pair[k][0], position_pair[k][1] + 1):
                if img[y, x, 0] == 255:
                    y_bottom.append(y)
                    bottom_flag = True
                    break
            if bottom_flag is True:
                break
        top_flag = False
        bottom_flag = False
    return y_top, y_bottom
