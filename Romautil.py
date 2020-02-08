import romkan
import pygame
import re


def is_readable_key_pressed(code) -> bool:
    """
    Returns whether alphabet, numeber, or "-" key pressed or not.

    :param code: keycode, which can acquired from pygame.event.get()[n].key
    :return: True if readable key pressed, or else returns False
    """

    if chr(code) == "-": return True

    if not chr(code).isalnum(): return False
    if not chr(code).islower(): return False
    if pygame.key.get_mods(): return False
    return True


def hira2roma(str) -> str:
    """
    Convert hiragana string into roma string

    :param str: hiragana string
    :return: roma string
    """
    target_roma = romkan.to_kunrei(str)

    # romkan.to_kunrei() returns in the not suitable format;
    # its return value contains "n'" if two "n" is exactly required for "ん".
    # e.g.)なんでやねん -> nandeyanen
    # e.g.)なんのこと   -> nan’nokoto
    target_roma = re.sub("(.)\'", "\\1\\1", target_roma)

    return target_roma


def get_not_halfway_hr(full_hiragana, progress_roma):
    """
    Returns the correct hiragana notation during typing.

    :param full_hiragana: FULL hiragana text
    :param progress_roma: romaji
    """

    if len(progress_roma) == 0: return ""
    romaji = hira2roma(full_hiragana)

    index = romaji.find(progress_roma)

    if re.match("[aeiouyn]", romaji[index]) and romkan.is_consonant(romaji[index - 1]):
        return romkan.to_hiragana(romaji[index - 1:])

    return romkan.to_hiragana(romaji[index:])