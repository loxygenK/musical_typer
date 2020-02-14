import pygame
from PIL import Image, ImageDraw
from math import tan, radians
from ColorTheme import *

import time


@DeprecationWarning
def arc(surface, color, pos, radius, start_angle, stop_angle, width = 1):

    lu = (pos[0] - radius, int(pos[1] + tan(radians(135)) * radius))
    rd = (pos[0] + radius, int(pos[1] - tan(radians(-45)) * radius))

    rect = (*lu, *rd)



    # 0.9ms
    im = Image.new("RGBA", (rd[0] - lu[0] + 1, rd[1] - lu[1]))
    draw = ImageDraw.Draw(im, "RGBA")

    draw.arc((0, 0, rd[0] - lu[0], rd[1] - lu[1]), start_angle, stop_angle, fill=color, width=5)
    byte = im.tobytes("raw")
    start = time.time()
    pyg_im = pygame.image.fromstring(byte, im.size, "RGBA")
    print(time.time() - start)


    surface.blit(pyg_im, lu)


def write_limit(screen, pos, left_limit, font, str, color=TEXT_COLOR):
    """
    左方向に描画制限を設けて、右揃えで文字列を描画する。

    :param screen: 描画対象スクリーン
    :param font: フォント
    :param str: 描画する文字
    :param left_limit: 左方向の制限X
    :param right: 描画基準X
    :param y: 描画基準Y
    :return: なし
    """
    rect_typed = font.render(str, True, color)

    if rect_typed.get_width() > (pos[0] - left_limit):
        screen.blit(rect_typed, (left_limit, pos[1]),
                       (rect_typed.get_width() - (pos[0] - left_limit), 0, rect_typed.get_width(), rect_typed.get_height()))
    else:
        screen.blit(rect_typed, (pos[0] - rect_typed.get_width(), pos[1]))

def print_progress(screen, pos, left_limit, font, typed, remain, past_color=None, remain_color=None):
    """
    タイピングの途中経過を描画する。

    :param screen: 描画対象スクリーン
    :param font: フォント
    :param typed: タイプした文字
    :param remain: 残っている文字
    :param left_limit: 左方向の制限X
    :param right: 描画基準X
    :param y: 描画基準Y
    :return:
    """

    if past_color is None:
        past_color = more_whiteish(TEXT_COLOR, 100)
    if remain_color is None:
        remain_color = TEXT_COLOR

    write_limit(screen, pos, left_limit, font, typed, past_color)
    rect_nottyped = font.render(remain, True, remain_color)
    screen.blit(rect_nottyped, pos, (0, 0, (pos[0] - left_limit), rect_nottyped.get_height()))