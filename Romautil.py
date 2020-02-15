##################################
#                                #
#   loxygenK/musical_typer       #
#   ローマ字関係ユーティリティ   #
#   (c)2020 loxygenK             #
#      All right reversed.       #
#                                #
##################################

import re

import pygame
import romkan


def is_readable_key_pressed(code) -> bool:
    """
    押されたキーがアルファベットキー、数字キー、「-」キーのいずれかかを判断する。

    :param code: pygame.event.get()[n].keyから取得できる文字コード。
    :return: 上記の条件に当てはまればTrue、なければFalse
    """

    if chr(code) == "-": return True

    if not chr(code).isalnum(): return False
    if not chr(code).islower(): return False
    if pygame.key.get_mods(): return False
    return True


def hira2roma(str) -> str:
    """
    ひらがなを訓令式ローマ字に変換する

    :param str: ひらがな
    :return: 訓令式ローマ字
    """
    target_roma = romkan.to_kunrei(str)

    # romkan.to_kunrei() は使用できない形式で値を返す：
    # 「ん」のタイプに際し、２つ「n」をタイプしなければならない場合は、
    # 「n'」と表記している。
    # e.g.)なんでやねん -> nandeyanen
    # e.g.)なんのこと   -> nan’nokoto
    target_roma = re.sub("(.)\'", "\\1\\1", target_roma)

    # ふが絶対に「fu」で返ってきてしまう。
    target_roma = target_roma.replace("fu", "hu")

    return target_roma


def get_not_halfway_hr(full_hiragana, progress_roma):
    """
    入力中に対しても正しいひらがな表記を取得する。

    :param full_hiragana: 「全体の」ひらがな
    :param progress_roma: ローマ字
    """

    if len(progress_roma) == 0: return ""
    romaji = hira2roma(full_hiragana)

    index = romaji.rfind(progress_roma)

    if re.match("[aeiouyn]", romaji[index]) and romkan.is_consonant(romaji[index - 1]):
        if len(romaji) >= 2 and romkan.is_consonant(romaji[index - 2]):
            return romkan.to_hiragana(romaji[index - 2:])[1:]
        else:
            return romkan.to_hiragana(romaji[index - 1:])

    return romkan.to_hiragana(romaji[index:])


def is_halfway(hiragana, english):
    """
    タイピングが中途半端(ひらがなの途中)か確認する。

    :param hiragana: 「全体の」ひらがな
    :param english: ローマ字
    :return: 中途半端であった場合はTrueを返す。
    """
    return hira2roma(get_not_halfway_hr(hiragana, english))[:1] != hira2roma(english)[:1]
