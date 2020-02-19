##################################
#                                #
#   loxygenK/musical_typer       #
#   エフェクターメソッド         #
#   (c)2020 loxygenK             #
#      All rights reversed.       #
#                                #
##################################
import pygame

from lib.GameSystem import Screen


def absolute_fadeout(current_frame, total_frame, ui: Screen, args):
    """
    スライドして消えていく文字を描画する。座標は絶対指定。
    """
    color = args[1] + (255 * (current_frame / total_frame),)

    ui.print_str(args[4], args[5] - args[3] * (current_frame / total_frame), args[2], args[0], color)


def slide_fadeout_text(current_frame, total_frame, ui: Screen, args):
    """
    スライドして消えていく文字を描画する。
    """
    w, h = pygame.display.get_surface().get_size()

    color = args[1] + (255 * (current_frame / total_frame),)

    text = args[2].render(args[0], True, color)
    text_w, text_h = text.get_size()

    ui.print_str(
        (w - text_w) / 2 + args[4],
        (h - text_h) / 2 + args[5] - args[3] * (current_frame / total_frame),
        args[2],
        args[0],
        color
    )


def blink_rect(current_frame, total_frame, ui: Screen, args):
    """
    画面の指定した領域を一回点滅させる。
    """

    color = args[0] + (255 - 255 * (current_frame / total_frame),)

    size = (args[1][2], args[1][3])

    alpha_info = pygame.Surface(size, pygame.SRCALPHA)
    alpha_info.fill((255, 255, 255, 255 - 255 * (current_frame / total_frame)), special_flags=pygame.BLEND_RGBA_MULT)
    filler = pygame.Surface(size)
    filler.fill(color)
    filler.set_alpha(255 - 255 * (current_frame / total_frame))
    filler.blit(alpha_info, (0, 0))
    ui.screen.blit(filler, (args[1][0], args[1][1]))


def print_text(_, __, ui: Screen, args):
    """
    画面に文字列を表示する。
    """

    ui.print_str(args[0], args[1], args[2], args[3], args[4])


def faded_text(current_frame, total_frame, ui: Screen, args):
    """
    指定した位置から動かずにフェードアウトしていく文字列を表示する。
    """

    ui.print_str(args[0], args[1], args[2], args[3], (*args[4], 255 * (current_frame / total_frame)))
