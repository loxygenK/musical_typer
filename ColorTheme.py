BACKGROUND = (255,243,224)
GREEN_THICK_COLOR = (0,77,64)
GREEN_THIN_COLOR = (178,255,89)
BLUE_THICK_COLOR = (63,81,181)
TEXT_COLOR = (56,56,62)


def more_whiteish(base_color, delta):
    return tuple(min(x + delta, 255) for x in base_color)


def more_blackish(base_color, delta):
    return tuple(max(x - delta, 0) for x in base_color)