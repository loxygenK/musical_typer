import pygame
import pygame_misc
import Romautil

class Screen:
    """
    画面処理を簡単にするためのクラス。
    このクラスのインスタンスは画面そのものも持つ
    """

    nihongo_font = pygame.font.Font("mplus-1m-medium.ttf", 48)
    alphabet_font = pygame.font.Font("mplus-1m-medium.ttf", 32)
    full_font = pygame.font.Font("mplus-1m-medium.ttf", 24)
    system_font = pygame.font.Font("mplus-1m-medium.ttf", 16)

    def __init__(self):
        self.screen = pygame.display.set_mode((600, 480))
        pygame.display.set_caption("Musical Typer")

    def print_str(self, x, y, font, text, color=(255, 255, 255)):
        pygame_misc.print_str(self.screen, x, y, font, text, color)


class GameProgressInfo:
    """
    ゲームの進行情報を保持するクラス。
    """

    def __init__(self, score):

        self.lyrincs_index = -1
        """今いる歌詞のインデックス。 get_current_lyrincsメソッドにより更新される"""

        self.zone_index = -1
        """今いるゾーンのインデックス。 get_zone_lyrincsメソッドにより更新される"""
        self.score = score

    def next_lyrincs_incoming(self, pos):
        """
        与えられた時間において、次の歌詞が来ているか。

        :param pos: 現在の時間
        :return: 次の歌詞が来ている場合にTrue
        """
        return self.score.score[self.lyrincs_index + 1][0] <= pos

    def next_zone_incoming(self, pos):
        """
        与えられた時間に置いて、次のゾーンが来ているか。

        :param pos: 現在の時間
        :return: 次のゾーンが来ている場合にTrue
        """
        return self.score.score[self.zone_index + 1][0] <= pos

    def get_current_lyrincs(self, pos):
        """
        与えられた時間に置いて打つべき歌詞のデータを求める。

        :param pos: 現在の時間
        :return: データ, lyrincs_indexが変化したか
        """

        # TODO: 処理を軽くする(キャッシュとか使って)
        for i in range(len(self.score.score)):


            if self.score.score[i][0] >= pos:

                is_lidx_changes = (i - 1) != self.lyrincs_index
                if is_lidx_changes:
                    self.lyrincs_index = i - 1
                return self.score.score[i - 1], is_lidx_changes

        return None

    def get_current_zone(self, pos):
        """
        与えられた時間が属するゾーンを求める。

        :param pos: 現在の時間
        :return: ゾーン名。ゾーンに属していない場合はNoneを返す
        """
        # TODO: 処理を軽くする(キャッシュとか使って)
        for i in range(len(self.score.zone)):

            if self.score.zone[i][0] >= pos and self.score.zone[i][2] == "end":
                if self.score.zone[i - 1][0] <= pos and self.score.zone[i - 1][2] == "start":
                    return self.score.zone[i][1]
                else:
                    return None

        return None

    def get_sentence_full_time(self):
        """
        現在の歌詞が表示される時間を求める。

        :return: 現在の歌詞時間。
        """
        next_sentence_time = self.score.score[self.lyrincs_index + 1][0]
        this_sentence_time = self.score.score[self.lyrincs_index][0]

        return next_sentence_time - this_sentence_time

    def get_sentence_elasped_time(self, pos):
        """
        現在の歌詞が表示されてから経った時間を求める。

        :param pos: 現在の時間
        :return: 経った時間。
        """

        next_sentence_time = self.score.score[self.lyrincs_index + 1][0]
        return next_sentence_time - pos

    def get_time_remain_ratio(self, pos):
        """
        0～1で、どのくらい時間が経ったかを求める。

        :param pos: 現在時間
        :return: 経った時間を0～1で。
        """
        return self.get_sentence_elasped_time(pos) / self.get_sentence_full_time()


class GameJudgementInfo:
    """
    スコアやタイプ成功回数／失敗回数を管理する。
    """

    ONE_CHAR_POINT = 10
    PERFECT_POINT = 100
    CLEAR_POINT = 50
    MISS_POINT = -30
    COULDNT_TYPE_POINT = -2

    def __init__(self):
        self.target_roma = ""
        self.target_kana = ""
        self.full = ""

        self.count = 0
        self.missed = 0

        self.sent_miss = 0
        self.sent_count = 0

        self.point = 0

        self.completed = True


    def get_sentence_missrate(self):
        """
        歌詞ごとの成功比率を求める。
        成功回数+失敗回数が0の場合は、成功回数を返す。(つまり0になる)
        :return: 成功比率（成功回数/(成功回数+失敗回数)）
        """

        trying_sumup = self.sent_miss + self.sent_count

        # To prevent ZeroDivision
        if trying_sumup == 0:
            trying_sumup = 1

        return self.sent_count / trying_sumup

    def set_current_lyrinc(self, full, kana):
        """
        現在打つべき歌詞を設定する。kanaのローマ字変換結果が0文字だった場合は、self.completed はFalseになる。

        :param full: 歌詞
        :param kana: 歌詞のふりがな
        :return: なし
        """

        self.full = full
        self.target_kana = kana
        self.target_roma = Romautil.hira2roma(self.target_kana)

        if len(self.target_roma) == 0:
            self.completed = True


    def reset_sentence_score(self):
        """
        歌詞ごとの進捗情報を消去する。

        :return: なし
        """
        self.sent_count= 0
        self.sent_miss = 0
        self.completed = False

    def count_success(self):
        """
        タイプ成功をカウントする。

        :return: このカウントで完了した場合にはTrue、していない場合にはFalse。
        """

        self.count += 1
        self.point += GameJudgementInfo.ONE_CHAR_POINT
        self.sent_count += 1

        self.target_roma = self.target_roma[1:]
        self.target_kana = Romautil.get_not_halfway_hr(self.target_kana, self.target_roma)

        if len(self.target_roma) == 0:
            self.point += GameJudgementInfo.CLEAR_POINT
            if self.sent_miss == 0:
                self.point += GameJudgementInfo.PERFECT_POINT
            self.completed = True

            return True
        return False

    def count_failure(self):
        """
        失敗をカウントする。

        :return: なし
        """
        self.missed += 1
        self.sent_miss += 1
        self.point += GameJudgementInfo.MISS_POINT

    def is_expected_key(self, code):
        """
        タイプされたキーが期待されているキーか確認する。

        :param code: タイプされたキー
        :return: 正しい場合はTrue
        """

        if len(self.target_roma) == 0:
            return False

        print(code, end="")

        return self.target_roma[0] == code


class SEControl:
    success = pygame.mixer.Sound("ses/success.wav")
    failed = pygame.mixer.Sound("ses/failed.wav")
    unneccesary = pygame.mixer.Sound("ses/unneccesary.wav")