##############################
#                            #
#   loxygenK/musical_typer   #
#   ゲームシステム           #
#   (c)2020 loxygenK         #
#      All rights reversed.   #
#                            #
##############################

import re

import chardet
import pygame
import romkan

from lib import Romautil


class ScoreFormatError(Exception):

    def __init__(self, line, text):
        super(ScoreFormatError, self).__init__(text + " at line " + str(line) + ".")

    pass


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

    FOREGROUND_EFFECTOR = 0
    BACKGROUND_EFFECTOR = 1

    def __init__(self):
        self.screen = pygame.display.set_mode((640, 530))
        self.effector: list = [{}, {}]
        pygame.display.set_caption("Musical Typer")

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

        rect = font.render(text, True, color)
        if len(color) == 4:
            alpha_info = pygame.Surface(rect.get_size(), pygame.SRCALPHA)
            alpha_info.fill((255, 255, 255, 255 - color[3]))
            surf = rect.copy()
            surf.blit(alpha_info, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self.screen.blit(surf, (x, y))
        else:
            self.screen.blit(rect, (x, y))

    def add_effector(self, mode, living_frame, section_name, draw_func, argument=None):
        """
        エフェクターを追加する。
        :param mode: 前面なら0、背景なら1
        :param living_frame: 生存時間
        :param section_name: エフェクターのセクション名
        :param draw_func: 描画メソッド
        :param argument: 描画メソッドに渡す引数
        :return: なし
        """

        # if draw_func.__name__ in self.fg_effector.keys() は遅い:/
        try:
            del self.effector[mode][draw_func.__name__ + section_name]
        except KeyError:
            pass

        self.effector[mode].setdefault(draw_func.__name__ + section_name, [living_frame, 0, draw_func, argument])

    def update_effector(self, mode: int):
        """
        エフェクターを更新
        :param mode: 0なら前面エフェクターを更新する
                     1なら背面エフェクターを更新する
        :return: なし
        """
        key_list = list(self.effector[mode].keys())
        for k in key_list:
            self.effector[mode][k][2](
                self.effector[mode][k][1],
                self.effector[mode][k][0],
                self,
                self.effector[mode][k][3]
            )
            self.effector[mode][k][1] += 1

            if self.effector[mode][k][1] > self.effector[mode][k][0]:
                del self.effector[mode][k]


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

    def __init__(self, score, key_length=100):

        # 現在の歌詞／ゾーン／セクションの番号
        self.lyrics_index = -1
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

    # ----- メソッド -----

    # *** 現在の位置から情報を求める ***
    def update_current_lyrics_index(self, pos):
        """
        与えられた時間に置いて打つべき歌詞のデータを求める。

        :return: データ, lyrics_indexが変化したか
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
            if self.score.score[self.lyrics_index + 1][0] > pos:
                return False

        # 次の歌詞を探す
        #             pos i
        #              ↓ |
        # ---|//(i-1)/////|-----(i)-----|---
        #     └→ここが引っかかる
        for i in range(self.lyrics_index, len(self.score.score)):
            if i < 0:
                continue

            # i番目の歌詞の開始時間がposを超えているか
            if self.score.score[i][0] > pos:

                # 歌詞が変わっているか
                is_lidx_changes = i - 1 != self.lyrics_index
                if is_lidx_changes:
                    # 更新する
                    self.lyrics_index = i - 1

                # 歌詞が変わっているかどうかを返す
                return is_lidx_changes

        # ヒットしなかった(歌詞が終了した)
        if not self.song_finished:
            self.song_finished = True
            return True

        return False

    def update_current_section_index(self, pos):
        """
        与えられた時間に置いて打つべき歌詞のデータを求める。

        :return: データ, lyrics_indexが変化したか
        """

        if len(self.score.section) == 0:
            self.section_finished = True
            return False

        if self.section_index > len(self.score.section) - 1:
            return False
        else:
            if self.score.section[self.section_index + 1][0] > pos:
                return False

        for i in range(self.section_index, len(self.score.section)):
            if i < 0:
                continue

            if self.score.section[i][0] >= pos:

                is_lidx_changes = (i - 1) != self.section_index
                if is_lidx_changes:
                    self.section_index = i - 1
                return is_lidx_changes

        self.section_finished = True
        return False

    def update_current_zone_index(self, pos):
        """
        与えられた時間が属するゾーンを求める。

        :return: ゾーン名。ゾーンに属していない場合はNoneを返す
        """

        if len(self.score.zone) == 0:
            self.is_in_zone = False
            return

        if self.zone_index == len(self.score.zone) - 2:
            if self.score.zone[self.zone_index + 1][0] > pos:
                self.is_in_zone = True
                return
            else:
                self.is_in_zone = False
                return
        else:
            if self.score.zone[self.zone_index][0] <= pos < self.score.zone[self.zone_index + 1][0]:
                return

        for i in range(self.zone_index, len(self.score.zone)):
            if i < 0:
                continue

            if self.score.zone[i][0] >= pos and self.score.zone[i][2] == "end":
                if self.score.zone[i - 1][0] <= pos and self.score.zone[i - 1][2] == "start":

                    is_lidx_changes = (i - 1) != self.zone_index
                    if is_lidx_changes:
                        self.zone_index = i - 1

                    self.is_in_zone = True
                    return
                else:
                    if self.zone_index != 0:
                        self.zone_index = 0
                        self.is_in_zone = False
                        return

                    self.is_in_zone = False
                    return

        self.is_in_zone = False
        return

    # *** 残り時間情報 ***
    def get_time_remain_ratio(self, pos):
        """
        0～1で、どのくらい時間が経ったかを求める。

        :return: 経った時間を0～1で。
        """

        next_time = self.score.score[self.lyrics_index + 1][0]
        this_time = self.score.score[self.lyrics_index][0]

        return (next_time - pos) / (next_time - this_time)

    # *** ミス率 ****
    @staticmethod
    def calc_accuracy(count, miss):
        trying_sum_up = count + miss

        # ZeroDivisionを防ぐ
        if trying_sum_up == 0:
            trying_sum_up = 1

        return count / trying_sum_up

    def get_full_accuracy(self):
        """
        全体での成功比率を求める。
        成功回数+失敗回数が0の場合は、成功回数を返す。(つまり0になる)

        :return: 成功比率（成功回数/(成功回数+失敗回数)）
        """
        return self.calc_accuracy(self.count, self.missed)

    # *** 歌詞情報アップデート ***
    def update_lyrics_string(self, full=None, kana=None):
        """
        現在打つべき歌詞を設定する。kanaのローマ字変換結果が0文字だった場合は、self.completed はFalseになる。

        :param full: 歌詞
        :param kana: 歌詞のふりがな
        :return: なし
        """

        self.sent_count = 0
        self.sent_miss = 0
        self.typed_roma = ""
        self.completed = False

        if full is None:
            full = self.score.score[self.lyrics_index][1]

        if kana is None:
            kana = self.score.score[self.lyrics_index][2]

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

        if self.full[:1] == "/" and self.sent_count == 0:
            return

        self.point += GameInfo.COULDNT_TYPE_POINT * len(self.target_roma)
        self.standard_point += GameInfo.ONE_CHAR_POINT * len(self.target_roma) * 40
        self.standard_point += GameInfo.CLEAR_POINT + GameInfo.PERFECT_POINT

        self.missed += len(self.target_roma)
        self.sent_miss += len(self.target_roma)
        self.section_miss += len(self.target_roma)

    def reset_section_score(self):
        """
        セクションごとの進捗情報を消去する。

        :return: なし
        """
        self.section_count = 0
        self.section_miss = 0

    def count_success(self, pos):
        """
        タイプ成功をカウントする。
        """

        # スコア／理想スコアをカウントする
        self.count += 1
        self.sent_count += 1
        self.section_count += 1

        self.combo += 1

        self.point += int(GameInfo.ONE_CHAR_POINT * 10 * self.get_key_per_second() * (self.combo / 10))

        # self.point += int(10 * self.get_key_per_second())

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
            self.key_type_tick(pos)

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

        # l? は x? でもOK
        if self.target_roma[0] == "x":
            return code == "x" or code == "l"

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
                return True
            elif hepburn[0] == code:
                self.target_roma = hepburn + self.target_roma[len(kunrei):]
                return True
            elif optimized[0] == code:
                self.target_roma = optimized + self.target_roma[len(kunrei):]
                return True
            else:
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

        if accuracy == -1:
            accuracy = self.get_full_accuracy()

        score = self.point * accuracy

        if score <= 0:
            return 0

        if limit:
            score = min(score, self.standard_point)

        return score / self.standard_point

    def calculate_rank(self, accuracy=-1):
        """
        達成率からランクのIDを取得する

        :param accuracy: 計算に使用する達成率。
        :return: ランクのID
        """
        rank_standard = [200, 150, 125, 100, 99.50, 99, 98, 97, 94, 90, 80, 60, 40, 20, 10, 0]

        rate = self.get_rate(accuracy)

        for i in range(0, len(rank_standard)):
            if rank_standard[i] < rate * 100:
                return i
        return len(rank_standard) - 1

    def key_type_tick(self, pos):
        """
        キータイプを記録する。
        :return: なし
        """

        if self.prev_time == 0:
            self.prev_time = pos
            return

        self.key_log.append(pos - self.prev_time)
        self.prev_time = pos

        if len(self.key_log) > self.length:
            del self.key_log[0]

    def get_key_per_second(self):
        """
        一秒ごとにタイプするキーを求める。

        :return: [key/sec]
        """
        if len(self.key_log) == 0:
            return 0

        return 1 / (sum(self.key_log) / len(self.key_log))


class SoundEffectConstants:
    """
    効果音ファイルの集合体。
    """
    success = pygame.mixer.Sound("ses/success.wav")
    special_success = pygame.mixer.Sound("ses/special.wav")
    failed = pygame.mixer.Sound("ses/failed.wav")
    unnecessary = pygame.mixer.Sound("ses/unnecessary.wav")
    game_over = pygame.mixer.Sound("ses/game_over.wav")
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
        re_rect_bracket = re.compile(r"\[(.*)\]")

        # エンコードを判別する
        with open(file_name, mode="rb") as f:
            detect_result = chardet.detect(f.read())

        encoding = detect_result["encoding"]

        # ファイルを読み込む
        with open(file_name, mode="r", encoding=encoding) as f:
            lines = f.readlines()

        # ----- [ パース ] -----

        current_minute = 0
        current_time = 0

        song = ""
        phon = ""

        is_in_song = False

        for i in range(len(lines)):

            line = lines[i].strip()

            # ----- 処理対象行かの確認

            # コメント
            if line.startswith("#"):
                continue

            # 空行
            if len(line) == 0:
                continue

            # カギカッコ
            rect_blk_match = re_rect_bracket.match(line)

            # ----- 曲外での処理

            if not is_in_song:

                # 曲に関するプロパティ
                if line.startswith(":") and not is_in_song:
                    line = line[1:]
                    key, value = line.split()

                    if key in self.properties.keys():
                        self.log.append([Score.LOG_ERROR, i + 1, "Duplicated song properties!"])
                        self.re_initialize_except_log()
                        break
                    else:
                        self.properties.setdefault(key, value)
                    continue

                if rect_blk_match is not None:
                    command = rect_blk_match[1]

                    # 曲開始コマンド?
                    if command == "start":
                        is_in_song = True
                        continue

                # 上記の条件にヒットしない文字列は、
                # 曲データの外では許可されない
                self.log.append([Score.LOG_ERROR, i + 1, "Unknown text outside song section"])
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
                        self.log.append([Score.LOG_ERROR, i + 1, "No pronunciation data"])
                        self.re_initialize_except_log()
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

        # エラーは出ていないか
        if len(list(filter(lambda x: x[0] == Score.LOG_ERROR, self.log))) == 0:
            # wavは定義されているか
            if "song_data" not in self.properties.keys():
                # それはダメ
                raise ScoreFormatError(0, "Song is not specified")
            else:
                # 読み込む
                pygame.mixer.music.load(self.properties["song_data"])
        else:
            # エラーなので例外をスローする
            raise ScoreFormatError(self.log[0][1], self.log[0][2])
