##############################
#                            #
#   loxygenK/musical_typer   #
#   デザイン関係定数         #
#   (c)2020 loxygenK         #
#      All right reversed.   #
#                            #
##############################

BACKGROUND_COLOR = (255,243,224)
RED_COLOR = (250,119,109)
GREEN_THICK_COLOR = (0,77,64)
GREEN_THIN_COLOR = (178,255,89)
BLUE_THICK_COLOR = (63,81,181)
BLUE_THICK_COLOR = (63,81,181)
TEXT_COLOR = (56,56,62)

MARGIN = 15

def more_whiteish(base_color, delta):
    """
    指定した色よりも指定した数値分白めの色を取得する。

    :param base_color: ベースとなる色
    :param delta: どのくらい白くするかをRGBで
    :return: RGB各値にdeltaを足したもの
    """
    return tuple(min(x + delta, 255) for x in base_color)


def more_blackish(base_color, delta):
    """
    指定した色よりも指定した数値分黒めの色を取得する。

    :param base_color: ベースとなる色
    :param delta: どのくらい黒くするかをRGBで
    :return: RGB各値にdeltaを引いたもの
    """
    return tuple(max(x - delta, 0) for x in base_color)


def invert_color(base_color):
    """
    RGB的な意味で反対の色を取得する。補色じゃないので注意。

    :param base_color: ベースとなる色
    :return: 255からRGB各値を引いたもの。
    """
    return tuple(255 - x for x in base_color)