import pygame
from PIL import Image, ImageDraw
from math import tan, radians
from ColorTheme import *

def arc(surface, color, pos, radius, start_angle, stop_angle, width = 1):

    lu = (pos[0] - radius, int(pos[1] + tan(radians(135)) * radius))
    rd = (pos[0] + radius, int(pos[1] - tan(radians(-45)) * radius))

    rect = (*lu, *rd)

    im = Image.new("RGBA", (rd[0] - lu[0] + 1, rd[1] - lu[1]))
    draw = ImageDraw.Draw(im, "RGBA")

    draw.arc((0, 0, rd[0] - lu[0], rd[1] - lu[1]), start_angle, stop_angle, fill=color, width=5)

    pyg_im = pygame.image.fromstring(im.tobytes("raw"), im.size, "RGBA")

    surface.blit(pyg_im, lu)


def write_limit(screen, font, str, left_limit, right, y):
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
    rect_typed = font.render(str, True, more_whiteish(TEXT_COLOR, 100))

    if rect_typed.get_width() > (right - left_limit):
        screen.blit(rect_typed, (left_limit, y),
                       (rect_typed.get_width() - (right - left_limit), 0, rect_typed.get_width(), rect_typed.get_height()))
    else:
        screen.blit(rect_typed, (right - rect_typed.get_width(), y))

def print_progress(screen, font, typed, remain, left_limit, right, y):
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
    write_limit(screen, font, typed, left_limit, right, y)
    rect_nottyped = font.render(remain, True, TEXT_COLOR)
    screen.blit(rect_nottyped, (right, y), (0, 0, (right - left_limit), rect_nottyped.get_height()))