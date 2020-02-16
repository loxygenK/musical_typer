import pygame
from PIL import Image, ImageDraw
from math import tan, radians

from ColorTheme import *


##############################
#                            #
#   loxygenK/musical_typer   #
#   描画関係ユーティリティ   #
#   (c)2020 loxygenK         #
#      All right reversed.   #
#                            #
##############################

class KeyboardDrawer:
    """
    キーボード描画クラス
    """
    keyboard = ["1234567890-\\^", "qwertyuiop@[", "asdfghjkl;:]", "zxcvbnm,./\\"]
    highlight_text = "fj"

    def __init__(self, screen, start_y, font, key_size, key_margin, width = 1, background_color = None):
        """
        キーボード描画クラスを初期化する。
        
        :param screen: 描画対象ウィンドウ
        :param start_y: 描画開始Y
        :param font: キー文字に使用するフォント
        :param key_size: 一つ一つのキーの大きさ
        :param key_margin: キーの間の余白
        :param width: キーの枠
        :param background_color: キーの背景色
        """
        self.screen = screen
        self.start_y = start_y
        self.font = font
        self.key_size = key_size
        self.key_margin = key_margin
        self.width = width
        self.background_color = background_color
        pass

    def get_place(self, key_char):
        w, h = pygame.display.get_surface().get_size()
        size = self.key_size + self.key_margin
        for i in range(4):
            key = self.keyboard[i]
            start = (w - size * len(key)) / 2
            index = key.find(key_char)
            if index != -1:
                y = self.start_y + i * size
                x = start + index * size
                return (x, y)

        return None

    def draw(self, highlight="", *, screen=None, start_y=-1, font=None, key_size=-1, key_margin=-1, width=-1, background_color=(-1, -1, -1)):
        """
        キーボードに描画を行う。
        
        :param highlight: ハイライト対象のキー
        :param screen: [略]描画対象ウィンドウ
        :param start_y: [略]描画開始Y
        :param font: [略]キー文字に使用するフォント
        :param key_size: [略]一つ一つのキーの大きさ
        :param key_margin: [略]キーの間の余白
        :param width: [略]キーの枠
        :param background_color: [略]キーの背景色
        :return: なし
        """

        # フィールドから継承する値を取得する
        if screen           is None:         screen = self.screen
        if start_y          is -1:           start_y = self.start_y
        if font             is None:         font = self.font
        if key_size         is -1:           key_size = self.key_size
        if key_margin       is -1:           key_margin = self.key_margin
        if width            is -1:           width = self.width

        if background_color is not None and background_color[0] == -1:
            background_color = self.background_color

        w, h = pygame.display.get_surface().get_size()
        size = key_size + key_margin
        for i in range(4):
            key = self.keyboard[i]
            start = (w - size * len(key)) / 2
            for j in range(len(key)):
                is_highlight_needed = (highlight != "" and highlight.lower() == key[j].lower())
                if is_highlight_needed:
                    pygame.draw.rect(screen, GREEN_THICK_COLOR,
                                 (start + size * j, start_y + size * i, key_size, key_size), 0)
                elif background_color is not None:
                    pygame.draw.rect(screen, background_color,
                                 (start + size * j, start_y + size * i, key_size, key_size), 0)

                pygame.draw.rect(screen, TEXT_COLOR,
                                 (start + size * j, start_y + size * i, key_size, key_size), width)

                color = TEXT_COLOR
                if is_highlight_needed:
                    color = invert_color(TEXT_COLOR)
                elif key[j] in self.highlight_text:
                    color = BLUE_THICK_COLOR

                chr = font.render(key[j].upper(), True, color)
                screen.blit(chr, (start + size * j + key_size // 2 - chr.get_width() // 2, start_y + size * i + key_size // 2 - chr.get_height() // 2))


@DeprecationWarning
def arc(surface, color, pos, radius, start_angle, stop_angle, width = 1):
    """
    弧を描画する。めちゃくちゃ重いので使わないほうがいい。

    :param surface: 描画先Surface
    :param color: 色
    :param pos: 中心位置
    :param radius: 半径
    :param start_angle: 開始角
    :param stop_angle: 終了角
    :param width: 枠の太さ
    :return: なし
    """

    lu = (pos[0] - radius, int(pos[1] + tan(radians(135)) * radius))
    rd = (pos[0] + radius, int(pos[1] - tan(radians(-45)) * radius))

    im = Image.new("RGBA", (rd[0] - lu[0] + 1, rd[1] - lu[1]))
    draw = ImageDraw.Draw(im, "RGBA")

    draw.arc((0, 0, rd[0] - lu[0], rd[1] - lu[1]), start_angle, stop_angle, fill=color, width=5)
    byte = im.tobytes("raw")
    pyg_im = pygame.image.fromstring(byte, im.size, "RGBA")

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


def write_center_x(window, x, y, font, text, color=(255, 255, 255)):
    """
    中央揃えで文字列を描画する。

    :param window: 描画先ウィンドウ
    :param x: 基準X
    :param y: Y
    :param font: 描画に使用するフォント
    :param text: 描画する文字列
    :param color: 描画する文字列の色
    :return: なし
    """

    rect = font.render(text, True, color)
    window.blit(rect, (x - rect.get_width() / 2, y))


def print_str(window, x, y, font, text, color=(255, 255, 255)):
    """
    画面に文字列を描画する。

    :param window: 描画先ウィンドウ
    :param x: 基準X
    :param y: Y
    :param font: 描画に使用するフォント
    :param text: 描画する文字列
    :param color: 描画する文字列の色
    :return: なし
    """
    rect = font.render(text, True, color)
    if len(color) == 4:
        alpha_info = pygame.Surface(rect.get_size(), pygame.SRCALPHA)
        alpha_info.fill((255, 255, 255, 255 - color[3]))
        surf = rect.copy()
        surf.blit(alpha_info, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        window.blit(surf, (x, y))
    else:
        window.blit(rect, (x, y))
