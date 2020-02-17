##############################
#                            #
#   loxygenK/musical_typer   #
#   ゲームシステム           #
#   (c)2020 loxygenK         #
#      All rights reversed.   #
#                            #
##############################

import re
import random

import chardet
import pygame
import romkan

import DrawingUtil
import Romautil


class Screen:
    """
    画面処理を簡単にするためのクラス。
    このクラスのインスタンスは画面そのものも持つ
    """

    big_font = pygame.font.Font("mplus-1m-medium.ttf", 72)
    nihongo_font = pygame.font.Font("mplus-1m-medium.ttf", 48)
    alphabet_font = pygame.font.Font("mplus-1m-medium.ttf", 32)
    full_font = pygame.font.Font("mplus-1m-medium.ttf", 24)
    rank_font = pygame.font.Font("mplus-1m-medium.ttf", 20)
    system_font = pygame.font.Font("mplus-1m-medium.ttf", 16)

    def __init__(self):
        self.screen = pygame.display.set_mode((640, 530))
        self.fg_effector: dict = {}
        self.bg_effector: dict = {}
        pygame.display.set_caption("Musical Typer")

    @property
    def screen_size(self):
        """
        スクリーンのサイズを返す。
        :return: (横幅, 縦幅)
        """
        return pygame.display.get_surface().get_size()

    def print_str(self, x, y, font, text, color=(255, 255, 255)):
        """
        ウィンドウに文字を描画する。

        :param x: X座標
        :param y: Y座標
        :param font: 描画に使用するフォント
        :param text: 描画する文字列
        :param color: 描画する色
        :return: なし
        """
        DrawingUtil.print_str(self.screen, x, y, font, text, color)
    
    def add_fg_effector(self, living_frame, section_name, draw_func, argument=None):
        """
        前面エフェクターを追加する。
        :param living_frame: 生存時間
        :param section_name: エフェクターのセクション名
        :param draw_func: 描画メソッド
        :param argument: 描画メソッドに渡す引数
        :return: なし
        """

        # if draw_func.__name__ in self.fg_effector.keys() は遅い:/
        try:
            del self.fg_effector[draw_func.__name__ + section_name]
        except:
            pass

        self.fg_effector.setdefault(draw_func.__name__ + section_name, [living_frame, 0, draw_func, argument])
    
    def add_bg_effector(self, living_frame, section_name, draw_func, argument=None):
        """
        背面エフェクターを追加する。
        :param living_frame: 生存時間
        :param section_name: エフェクターのセクション名
        :param draw_func: 描画メソッド
        :param argument: 描画メソッドに渡す引数
        :return: なし
        """

        # if draw_func.__name__ in self.fg_effector.keys() は遅い:/
        try:
            del self.bg_effector[draw_func.__name__ + section_name]
        except:
            pass

        self.bg_effector.setdefault(draw_func.__name__ + section_name, [living_frame, 0, draw_func, argument])

    def update_fg_effector(self):
        """
        前面エフェクターを更新する。
        :return: なし
        """

        key_list = list(self.fg_effector.keys())
        for k in key_list:
            self.fg_effector[k][2](self.fg_effector[k][1], self.fg_effector[k][0], self, self.fg_effector[k][3])
            self.fg_effector[k][1] += 1

            if self.fg_effector[k][1] > self.fg_effector[k][0]:
                del self.fg_effector[k]
    
    def update_bg_effector(self):
        """
        背面エフェクターを更新する。
        :return: なし
        """

        key_list = list(self.bg_effector.keys())
        for k in key_list:
            self.bg_effector[k][2](self.bg_effector[k][1], self.bg_effector[k][0], self, self.bg_effector[k][3])
            self.bg_effector[k][1] += 1

            if self.bg_effector[k][1] > self.bg_effector[k][0]:
                del self.bg_effector[k]

    @DeprecationWarning
    def get_font_by_size(self, size):
        """
        フォントをサイズから取得する。なんかそれなりに重いので使わんほうがいい
        使うなら何回も呼び出すんじゃなくて変数に入れるとかしよう

        :param size: サイズ
        :return: フォント
        """
        return pygame.font.Font("mplus-1m-medium.ttf", size)


class GameInfo:
    """
    ゲームの情報を統合して管理する。
    """

    ONE_CHAR_POINT = 10
    PERFECT_POINT = 100
    SECTION_PERFECT_POINT = 300
    SPECIAL_POINT = 50
    CLEAR_POINT = 50
    MISS_POINT = -30
    COULDNT_TYPE_POINT = -2

    IDEAL_TYPE_SPEED = 3.0

    rank_standard = [200, 150, 125, 100, 99.50, 99, 98, 97, 94, 90, 80, 60, 40, 20, 10, 0]
    rank_string = ["Wow", "Unexpected", "Very God", "God", "Pro", "Genius", "Geki-tsuyo", "tsuyotusyo", "AAA", "AA", "A", "B", "C", "D", "E", "F"]

    def __init__(self, score, key_length=100):

        # 現在位置
        self.pos = 0

        # 現在の歌詞／ゾーン／セクションの番号
        self.lyrincs_index =  -1
        self.zone_index = -1
        self.section_index = -1

        # すべての歌詞／セクションが打ち終わったか
        self.song_finished = False
        self.section_finished = False

        # ゾーン内にいるか
        self.is_in_zone = False

        # 譜面データ(点数じゃない)
        self.score = score

        # 歌詞データ
        self.target_roma = ""
        self.target_kana = ""
        self.full_kana = ""
        self.typed_roma = ""
        self.full = ""

        # 曲を通してのカウント／ミス
        self.count = 0
        self.missed = 0

        # 歌詞一文単位のカウント／ミス
        self.sent_miss = 0
        self.sent_count = 0

        # セクションごとのカウント／ミス
        self.section_miss = 0
        self.section_count = 0

        # リザルト
        self.sentence_log = []
        self.section_log = []

        # 現在の点数
        self.point = 0

        # 理想の点数
        self.standard_point = 0

        # これ以上タイプをする必要がないか
        self.completed = True

        # キータイプログ
        self.key_log = []
        self.prev_time = 0
        self.length = key_length

        # コンボ
        self.combo = 0

    # ----- プロパティ -----

    # *** タイプ情報 ***
    @property
    def typed_kana(self):
        """
        すでに打ったローマ字を取得する。

        :return: すでに打ったローマ字
        """

        typed_index = self.full_kana.rindex(self.target_kana)

        if len(self.target_kana) > 0:
            return self.full_kana[:typed_index]
        else:
            return self.full_kana

    @property
    def typed(self):
        """
        打ったキーの合計。

        :return: 打ったキーの合計
        """
        return self.count + self.missed

    @property
    def sent_typed(self):
        """
        文単位で打ったキーの数。
        :return: 打ったキー数
        """
        return self.sent_count + self.sent_miss

    @property
    def section_typed(self):
        """
        セクション単位で打ったキーの数。
        :return: 打ったキーの数
        """
        return self.section_count + self.section_miss

    @property
    def all_typed(self):
        """
        打ち終わったか(もともと歌詞がなかった場合はFalseを返す)
        :return: 歌詞がなく、一文字以上打っている場合はTrue
        """
        return self.completed and self.sent_typed > 0

    @property
    def is_ac(self):
        """
        ACしたか

        :return: GameInfo.all_typedを満たし、かつミス数が0で「ある」場合True
        """
        return self.completed and self.sent_typed > 0 and self.sent_miss == 0
    
    @property
    def is_wa(self):
        """
        WAだったか

        :return: GameInfo.all_typedを満たし、かつミス数が0で「ない」場合True
        """
        return self.completed and self.sent_typed > 0 and self.sent_miss > 0

    @property
    def has_to_prevent_miss(self):
        """
        輪唱をまだタイプしていない場合など、特殊なケースにより
        ミス判定をしてはいけない場合にTrueを返す。

        :return: ミス判定をしてはいけない場合にTrue
        """

        if self.full[:1] == "/" and self.sent_count == 0:
            return True

        return False

    # ----- メソッド -----

    # *** 現在の位置から情報を求める ***
    def update_current_lyrincs(self):
        """
        与えられた時間に置いて打つべき歌詞のデータを求める。

        :param pos: 現在の時間
        :return: データ, lyrincs_indexが変化したか
        """


        # 歌詞がない場合は無条件に終了する
        if len(self.score.score) == 0:
            self.song_finished = True
            return False

        # 一番最後の歌詞かどうか
        if self.song_finished:
            # 一番最後からは変化しない
            return False
        else:
            # 現在の歌詞がすでに終わっているか(次の歌詞の開始時間を過ぎているか)
            if self.score.score[self.lyrincs_index + 1][0] > self.pos:
                return False

        # 次の歌詞を探す
        #             pos i
        #              ↓ |
        # ---|//(i-1)/////|-----(i)-----|---
        #     └→ここが引っかかる
        for i in range(self.lyrincs_index, len(self.score.score)):
            if i < 0: continue


            # i番目の歌詞の開始時間がposを超えているか
            if self.score.score[i][0] > self.pos:

                # 歌詞が変わっているか
                is_lidx_changes = i - 1 != self.lyrincs_index
                if is_lidx_changes:

                    # 更新する
                    self.lyrincs_index = i - 1

                # 歌詞が変わっているかどうかを返す
                return is_lidx_changes

        # ヒットしなかった(歌詞が終了した)
        if not self.song_finished:
            self.song_finished = True
            return True

        return False

    def get_current_section(self):
        """
        与えられた時間に置いて打つべき歌詞のデータを求める。

        :param pos: 現在の時間
        :return: データ, lyrincs_indexが変化したか
        """

        if len(self.score.section) == 0:
            self.section_finished = True
            return False

        if self.section_index > len(self.score.section) - 1:
            return False
        else:
            if self.score.section[self.section_index + 1][0] > self.pos:
                return False

        for i in range(self.section_index, len(self.score.section)):
            if i < 0: continue

            if self.score.section[i][0] >= self.pos:

                is_lidx_changes = (i - 1) != self.section_index
                if is_lidx_changes:
                    self.section_index = i - 1
                return is_lidx_changes

        self.section_finished = True
        return False

    def update_current_zone(self):
        """
        与えられた時間が属するゾーンを求める。

        :param pos: 現在の時間
        :return: ゾーン名。ゾーンに属していない場合はNoneを返す
        """

        if len(self.score.zone) == 0:
            self.is_in_zone = False
            return False

        if self.zone_index == len(self.score.zone) - 2:
            if self.score.zone[self.zone_index + 1][0] > self.pos:
                self.is_in_zone = True
                return False
            else:
                self.is_in_zone = False
                return False
        else:
            if self.score.zone[self.zone_index][0] <= self.pos < self.score.zone[self.zone_index + 1][0]:
                return False

        for i in range(self.zone_index, len(self.score.zone)):
            if i < 0: continue

            if self.score.zone[i][0] >= self.pos and self.score.zone[i][2] == "end":
                if self.score.zone[i - 1][0] <= self.pos and self.score.zone[i - 1][2] == "start":

                    is_lidx_changes = (i - 1) != self.zone_index
                    if is_lidx_changes:
                        self.zone_index = i - 1

                    self.is_in_zone = True
                    return is_lidx_changes
                else:
                    if self.zone_index != 0:
                        self.zone_index = 0
                        self.is_in_zone = False
                        return True

                    self.is_in_zone = False
                    return False

        self.is_in_zone = False
        return False

    # *** 残り時間情報 ***
    def get_sentence_full_time(self):
        """
        現在の歌詞が表示される時間を求める。

        :return: 現在の歌詞時間。
        """
        next_sentence_time = self.score.score[self.lyrincs_index + 1][0]
        this_sentence_time = self.score.score[self.lyrincs_index][0]

        return next_sentence_time - this_sentence_time

    def get_sentence_elasped_time(self):
        """
        現在の歌詞が表示されてから経った時間を求める。

        :param pos: 現在の時間
        :return: 経った時間。
        """

        next_sentence_time = self.score.score[self.lyrincs_index + 1][0]
        return next_sentence_time - self.pos

    def get_time_remain_ratio(self):
        """
        0～1で、どのくらい時間が経ったかを求める。

        :param pos: 現在時間
        :return: 経った時間を0～1で。
        """
        return self.get_sentence_elasped_time() / self.get_sentence_full_time()

    # *** ミス率 ****
    def calc_accuracy(self, count, miss):
        trying_sumup = count + miss

        # ZeroDivisionを防ぐ
        if trying_sumup == 0:
            trying_sumup = 1

        return count / trying_sumup

    def get_full_accuracy(self):
        """
        全体での成功比率を求める。
        成功回数+失敗回数が0の場合は、成功回数を返す。(つまり0になる)

        :return: 成功比率（成功回数/(成功回数+失敗回数)）
        """
        return self.calc_accuracy(self.count, self.missed)

    def get_sentence_accuracy(self):
        """
        歌詞ごとの成功比率を求める。
        成功回数+失敗回数が0の場合は、成功回数を返す。(つまり0になる)
        :return: 成功比率（成功回数/(成功回数+失敗回数)）
        """

        return self.calc_accuracy(self.sent_count, self.sent_miss)

    # *** 歌詞情報アップデート ***
    def update_current_lyrics(self, full=None, kana=None):
        """
        現在打つべき歌詞を設定する。kanaのローマ字変換結果が0文字だった場合は、self.completed はFalseになる。

        :param full: 歌詞
        :param kana: 歌詞のふりがな
        :return: なし
        """

        self.reset_sentence_condition()

        if full is None:
            full = self.score.score[self.lyrincs_index][1]

        if kana is None:
            kana = self.score.score[self.lyrincs_index][2]

        self.full = full
        self.target_kana = kana
        self.full_kana = kana
        self.target_roma = Romautil.hira2roma(self.target_kana)

        if len(self.target_roma) == 0:
            self.completed = True

    def apply_TLE(self):
        """
        TLE計算をする
        :return: なし
        """

        if len(self.target_roma) == 0:
            return

        if self.has_to_prevent_miss:
            return

        self.point += GameInfo.COULDNT_TYPE_POINT * len(self.target_roma)
        self.standard_point += GameInfo.ONE_CHAR_POINT * len(self.target_roma) * 40
        self.standard_point += GameInfo.CLEAR_POINT + GameInfo.PERFECT_POINT

        self.missed += len(self.target_roma)
        self.sent_miss += len(self.target_roma)
        self.section_miss += len(self.target_roma)


    def get_section_missrate(self):
        """
        セクションごとの成功比率を求める。
        成功回数+失敗回数が0の場合は、成功回数を返す。(つまり0になる)
        :return: 成功比率（成功回数/(成功回数+失敗回数)）
        """

        return self.calc_accuracy(self.section_count, self.section_miss)

    def record_sentence_score(self):
        """
        歌詞ごとの進捗情報を記録する。

        :return: なし
        """
        self.sentence_log.append([self.sent_count, self.sent_miss, self.completed])

    def record_section_score(self):
        """
        セクションごとの進捗情報を記録する

        :return: なし
        """
        self.section_log.append([self.section_count, self.section_miss])

    def reset_sentence_condition(self):
        """
        歌詞ごとの進捗情報を消去する。

        :param count_tle: TLEを処理する
        :return: なし
        """
        
        self.sent_count = 0
        self.sent_miss = 0
        self.typed_roma = ""
        self.completed = False

    def reset_section_score(self):
        """
        セクションごとの進捗情報を消去する。

        :return: なし
        """
        self.section_count= 0
        self.section_miss = 0

    def count_success(self):
        """
        タイプ成功をカウントする。
        """

        # スコア／理想スコアをカウントする
        self.count += 1
        self.sent_count += 1
        self.section_count += 1

        self.combo += 1

        self.point += int(GameInfo.ONE_CHAR_POINT * 10 * self.get_key_per_second() * (self.combo / 10))
        ## self.point += int(10 * self.get_key_per_second())

        self.standard_point += int(GameInfo.ONE_CHAR_POINT * GameInfo.IDEAL_TYPE_SPEED * 10 * (self.combo / 10))

        # tech-zone ゾーン内にいるか
        if self.is_in_zone and self.score.zone[self.zone_index] == "tech-zone":
            self.point += self.SPECIAL_POINT

        # 歌詞情報を更新する
        self.typed_roma += self.target_roma[:1]
        self.target_roma = self.target_roma[1:]

        # 打つべきかなを取得する
        self.target_kana = Romautil.get_not_halfway_hr(self.target_kana, self.target_roma)

        # ひらがな一つのタイプが終了した?
        if not Romautil.is_halfway(self.target_kana, self.target_roma):
            # キータイプをカウントする
            self.keytype_tick()


        # これ以上打つ必要がないか
        if len(self.target_roma) == 0:

            # クリアポイントを付与
            self.point += GameInfo.CLEAR_POINT

            # ポイントを更新
            self.standard_point += GameInfo.CLEAR_POINT + GameInfo.PERFECT_POINT

            if self.sent_miss == 0:
                self.point += GameInfo.PERFECT_POINT

            self.completed = True

        return int(GameInfo.ONE_CHAR_POINT * 10 * self.get_key_per_second() * (self.combo / 10))


    def count_failure(self):
        """
        失敗をカウントする。

        :return: なし
        """
        self.missed += 1
        self.sent_miss += 1
        self.section_miss += 1
        self.point += GameInfo.MISS_POINT
        self.combo = 0

    def is_exactly_expected_key(self, code):
        """
        タイプされたキーが正確に期待されているキーか確認する。
        is_excepted_keyと違って、ローマ字表記の仕方の違いを許容しない。
        ゲーム内での判定では、is_expected_keyを使おう

        :param code: タイプされたキー
        :return: 正しい場合はTrue
        """

        if len(self.target_roma) == 0:
            return False

        return self.target_roma[0] == code

    def is_expected_key(self, code):
        """
        タイプされたキーが期待されているキーか確認する。

        :param code: タイプされたキー
        :return: 正しい場合はTrue
        """

        if len(self.target_roma) == 0:
            return False

        if not Romautil.is_halfway(self.target_kana, self.target_roma):

            first_syllable = Romautil.get_first_syllable(self.target_kana)
            kunrei = romkan.to_kunrei(first_syllable)
            hepburn = romkan.to_hepburn(first_syllable)
            optimized = Romautil.hira2roma(first_syllable)

            if kunrei[0] == "x":
                return self.is_exactly_expected_key(code)
            if kunrei[0] == code:
                print("Kunrei, approve.")
                return True
            elif hepburn[0] == code:
                print("Hepburn, approve.")
                self.target_roma = hepburn + self.target_roma[len(kunrei):]
                return True
            elif optimized[0] == code:
                print("Optimized, approve.")
                self.target_roma = optimized + self.target_roma[len(kunrei):]
                return True
            else:
                print("kunrei nor hepburn, deny.")
                return False
        else:
            return self.is_exactly_expected_key(code)

    def get_rate(self, accuracy=-1, limit=False):
        """
        達成率を計算する

        :param accuracy: 計算に使用する達成率情報。省略すると全体の達成率を使用する
        :param limit: 100%を超えないようにするか
        :return: 達成率
        """

        if accuracy == -1: accuracy = self.get_full_accuracy()

        standard = (self.standard_point + self.count * 45)
        score = self.point * accuracy

        if score <= 0: return 0

        if limit:
            score = min(score, standard)

        return score / standard

    def calcutate_rank(self, accuracy=-1):
        """
        達成率からランクのIDを取得する

        :param accuracy: 計算に使用する達成率。
        :return: ランクのID
        """

        rate = self.get_rate(accuracy)

        for i in range(0, len(self.rank_standard)):
            if self.rank_standard[i] < rate * 100:
                return i
        return len(self.rank_standard) - 1

    def keytype_tick(self):
        """
        キータイプを記録する。
        :return: なし
        """

        if self.prev_time == 0:
            self.prev_time = self.pos
            return

        self.key_log.append(self.pos - self.prev_time)
        self.prev_time = self.pos

        if len(self.key_log) > self.length:
            del self.key_log[0]

    def override_key_prev_pos(self, pos=-1):
        """
        前回のキータイプ時間を指定した時間で上書きする。

        :param pos: 上書きするキータイプ時間。省略すると現在の時間になる。
        :return: なし
        """
        self.prev_time = pos if pos != -1 else self.pos


    def get_key_type_average(self):
        """
        1つのキータイプに要する平均時間を求める
        :return: キータイプ時間
        """
        if len(self.key_log) == 0:
            return 0

        return sum(self.key_log) / len(self.key_log)

    def get_key_per_second(self):
        """
        一秒ごとにタイプするキーを求める。

        :return: [key/sec]
        """
        if len(self.key_log) == 0:
            return 0

        return 1 / self.get_key_type_average()


class SoundEffectConstants:
    """
    効果音ファイルの集合体。
    """
    success = pygame.mixer.Sound("ses/success.wav")
    special_success = pygame.mixer.Sound("ses/special.wav")
    failed = pygame.mixer.Sound("ses/failed.wav")
    unneccesary = pygame.mixer.Sound("ses/unneccesary.wav")
    gameover = pygame.mixer.Sound("ses/gameover.wav")
    ac = pygame.mixer.Sound("ses/ac.wav")
    wa = pygame.mixer.Sound("ses/wa.wav")
    fast = pygame.mixer.Sound("ses/fast.wav")
    tle = pygame.mixer.Sound("ses/tle.wav")


class Score:
    """
    譜面データ。
    """
    LOG_ERROR = 1
    LOG_WARN = 2

    def __init__(self):
        self.properties = {}
        self.log = []
        self.score = []
        self.zone = []
        self.section = []

    def log_error(self, line, text, init=True):
        """
        エラーログを記録し、データを削除する。
        :param line: ログを出力するときの行。
        :param text: ログ内容。
        :param init: データを削除するか(デフォルト: True)
        :return: なし
        """
        self.log.append([Score.LOG_ERROR, [line, text]])
        if init: self.re_initialize_except_log()

    def log_warn(self, line, text):
        """
        警告ログを記録する。
        :param line: ログを出力するときの行。
        :param text: ログ内容。
        :return: なし
        """
        self.log.append([Score.LOG_WARN, [line, text]])

    def re_initialize_except_log(self):
        """
        ログ以外を再初期化する。
        :return: なし
        """
        self.properties = {}
        self.score = []
        self.zone = []
        self.section = []

    def read_score(self, file_name):
        """
        ファイルから譜面データを読み込み、このインスタンスに値をセットする。
        :param file_name: 譜面データの入ったファイル
        :return: なし(このメソッドは破壊性である)
        """

        # ----- [ 下準備 ] -----

        # 便利なやつ
        re_rect_blacket = re.compile(r"\[(.*)\]")

        # エンコードを判別する
        detect_result = None

        with open(file_name, mode="rb") as f:
            detect_result = chardet.detect(f.read())

        encoding = detect_result["encoding"]

        # ファイルを読み込む
        lines = []
        with open(file_name, mode="r", encoding=encoding) as f:
            lines = f.readlines()

        # ----- [ パース ] -----

        current_minute = 0
        current_time = 0

        song = ""
        phon = ""

        is_in_song = False

        for line in lines:

            line = line.strip()

            # ----- 処理対象行かの確認

            # コメント
            if line.startswith("#"): continue

            # 空行
            if len(line) == 0: continue

            # カギカッコ
            rect_blk_match = re_rect_blacket.match(line)

            # ----- 曲外での処理

            if not is_in_song:

                # 曲に関するプロパティ
                if line.startswith(":") and not is_in_song:
                    line = line[1:]
                    key, value = line.split()
                    set_val_to_dictionary(self.properties, key, value)
                    continue

                if rect_blk_match is not None:
                    command = rect_blk_match[1]

                    # 曲開始コマンド?
                    if command == "start":
                        is_in_song = True
                        continue

                # 上記の条件にヒットしない文字列は、
                # 曲データの外では許可されない
                self.log_error(line, "Unknown text outside song section!")
                self.re_initialize_except_log()
                break

            # ----- 曲外での処理

            # カギカッコで囲まれているか
            if rect_blk_match is not None:
                command = rect_blk_match[1]
                # 間奏などで歌詞データがない
                if command == "break":
                    self.score.append([current_time, "", ""])
                    continue
                if command == "end":
                    self.score.append([current_time, ">>end<<", ""])
                    is_in_song = False
                    continue

            # 歌詞のみ(キャプションなど)
            if line.startswith(">>"):
                self.score.append([current_time, line[2:], ""])
                continue

            # 分指定演算子
            if line.startswith("|"):
                line = line[1:]
                current_minute = int(line)
                continue

            # 秒指定演算子
            # 秒指定演算子で、現在時間の更新と一緒に歌詞データの書き込みも実施する
            if line.startswith("*"):
                line = line[1:]

                # 歌詞データが提供されているのにも関わらず、ふりがなデータがない
                if len(song) != 0:
                    if len(phon) == 0:
                        # これはダメで、エラーを吐く
                        self.log_error(line, "No pronunciation data!")
                        break
                    else:
                        self.score.append([current_time, song, phon])

                # リセットする
                song = ""
                phon = ""

                # 現在時間をセットする
                current_time = 60 * current_minute + float(line)
                continue

            # セクション演算子
            if line.startswith("@"):
                line = line[1:]
                self.section.append([current_time, line])
                continue

            # ゾーン演算子
            if line.startswith("!"):
                line = line[1:]
                flag, zone_name = line.split()

                # ゾーンが始まる
                if flag == "start":
                    self.zone.append([current_time, zone_name, "start"])
                    continue
                # ゾーンが終わる
                elif flag == "end":
                    self.zone.append([current_time, zone_name, "end"])
                    continue

            # ふりがなデータ
            if line.startswith(":"):
                phon += line[1:]
                continue

            # 特に何もなければそれは歌詞
            song += line

        # 読み込み終わり
        self.score.insert(0, [0, "", ""])

        # 曲のwaveファイルが定義されているか
        if "song_data" not in self.properties.keys():
            # それはダメ
            self.log_error("[Loading song failed]", "No song specified!")
        else:
            # 読み込む
            pygame.mixer.music.load(self.properties["song_data"])


def set_val_to_dictionary(dict, key, value):
    """
    キーの有無に関わらず辞書にデータを書き込む。
    キーが辞書に無かった場合は追加し、すでにある場合は更新する。

    :param dict: 辞書
    :param key: キー
    :param value: 値
    :return:
    """
    if key in dict.keys():
        dict[key] = value
    else:
        dict.setdefault(key, value)
