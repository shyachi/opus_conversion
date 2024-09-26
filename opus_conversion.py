# このプログラムは入力の音楽ファイルのディレクトリー構成を保ったまま
# opusファイルに変換するプログラムです
# 別途必要な実行ファイル
# opusenc.exe : opusファイルを作成するのに必要です
# ffmpeg.exe : 様々な音楽ファイルをwavに変換し、opusenc.exeに渡すために必要です

import os
from os.path import expanduser
import subprocess
from tqdm import tqdm
import tkinter
from tkinter import filedialog
import datetime
from multiprocessing import Process, Queue, Pool
from queue import Empty
import re
from pathlib import Path, PurePath
import signal


# タグとカバーアート用のライブラリ群
from io import BytesIO
from PIL import Image
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from mutagen.oggopus import OggOpus


class WalkDirAndFiles:
    """
    ディレクトリーとファイルをリストアップたり、コピーしたりするクラス
    """
    def __init__(self, src:Path, dst:Path, target_file_type:list, dst_file_ext:list):
        """
        Args:
        src:入力ディレクトリー(Pathオブジェクト)
        dst:出力ディレクトリー(Pathオブジェクト)
        target_file_type:入力のフィルターを掛ける拡張子
        dst_file_ext:出力予定の拡張子
        """
        self.src_dir = src
        self.dst_dir = dst
        self.target_file_type = target_file_type
        self.dst_file_ext = dst_file_ext
        # ディレクトリーのリスト
        self.src_dir_list = []
        self.dst_dir_list = []
        # 入力ファイルのリスト
        self.src_file_list = []
        # 出力ファイルのリスト　[入力ファイル, 出力ファイル１, 出力ファイル２, ....]
        self.dst_file_list = []
    
    def walk_files(self, path:Path):
        """
        ディレクトリーを再帰的に検索、ファイルを見つけたら、file_listに追加する
        また、入力するファイルのフィルターを掛ける
        Args:
        path:入力ディレクトリー(Pathオブジェクト)
        file_list:pathの中に入っているファイルのリスト
        """
        for item in path.iterdir():
            if item.is_dir():
                self.walk_files(item)
            elif item.is_file():
                if item.suffix in self.target_file_type:
                    self.src_file_list.append(item)
    
    def walk_dirs(self, path:Path):
        """
        ディレクトリーを再帰的に検索、フォルダーを見つけたら、dir_listに追加する
        Args:
        path:入力ディレクトリー(Pathオブジェクト)
        dir_list:pathの中に入っているディレクトリーのリスト
        """
        for item in path.iterdir():
            if item.is_dir():
                self.src_dir_list.append(item)
                self.walk_dirs(item)
                
    def make_list(self):
        """
        各種リストを作成
        Args:
        set_ext:出力するファイルの拡張子
        filter_ext:フィルターする入力の拡張子
        """
        for dir in self.src_dir_list:
            pure_dir = PurePath(dir)
            sub_dir = pure_dir.relative_to(self.src_dir)
            output_dir = PurePath(self.dst_dir)
            self.dst_dir_list.append(output_dir / sub_dir)
        
        # 入力のファイルリストから出力のファイルリストを作成
        for file in self.src_file_list:
            # もし入力の拡張子と同じファイルがあれば
            if file.suffix in self.target_file_type:
                row_ext = []
                row_ext.append(file)
                for ext in self.dst_file_ext:
                    file_name = PurePath(f"{file.stem}{ext}")
                    pure_file = PurePath(file.parent)
                    sub_file = pure_file.relative_to(self.src_dir)
                    output_file = PurePath(self.dst_dir)
                    row_ext.append(output_file / sub_file / file_name)
                self.dst_file_list.append(row_ext)
    
    def make_dst_dirs(self):
        """
        出力先にディレクトリーを作成
        Args:
        """
        for dir in self.dst_dir_list:
            os.makedirs(dir, exist_ok=True)



TARGET_FILE_TYPE = [".flac",".mp3"]
DST_FILE_EXT = [".opus",".wav",".jpg"]

# 入力するディレクトリーのパスと、その上のディレクトリーの名前を取得
input_dir_pass = ""
# 出力するディレクトリーのパスと、その上のディレクトリーの名前を取得
output_dir_pass = ""

# Opusビットレート指定
bitrate = "96"

# マルチプロセス数指定
max_prosess_size = os.cpu_count() // 2

def write_log(write_text_list):
    # ログ用の初期化と作成
    print("ログを書き出します")
    now = datetime.datetime.now()
    log_file_name = now.strftime("Opus_Conversion_log_%y-%m-%d_%H%M%S.txt")
    os.makedirs("Log", exist_ok=True)
    log_file_pass = os.path.join("Log", log_file_name)
    
    with open(log_file_pass, mode='w', encoding="utf-8") as f:
        for text in write_text_list:
            f.write(text + "\n")
    
    print("ログの書き出しが完了しました。")

        
def export_coverart_img_and_tags(input_file_pass):
    """
    入力ファイルのカバーアートとタグを抽出して返す関数
    出力はtags(辞書形式)とカバーアートのタプル
    Args:
        input_file_pass (str): 入力ファイルのパス
    """
    filename, ext = os.path.splitext(input_file_pass)
    coverart_img = None
    tags_dict = None
    
    # tags_dict = ファイルに添付されているタグの辞書
    
    if ext == ".flac":
        tags_dict = FLAC(input_file_pass)
        # カバーアートの取得（FLAC）
        images = tags_dict.pictures
        if images is not None:
            # カバーアートは複数枚含まれているパターンがある
            # 最初の一枚だけ取得する
            for i, picture in enumerate(images):
                if i == 0:
                    coverart_img = Image.open(BytesIO(picture.data))
    elif ext ==".mp3":
        id3_temp = ID3(input_file_pass)
        tags_dict = EasyID3(input_file_pass)
        # カバーアートの取得（MP3）
        apic = id3_temp.get("APIC:")
        if apic is not None:
            coverart_img = Image.open(BytesIO(apic.data))
            
    return tags_dict, coverart_img

def insert_tags(opus_insert_file, tags):
    """
    入力Opusファイルにタグとカバーアートを書き込む
    出力は入力ファイルへの上書き
    Args:
        opus_insert_file (str): 入力Opusファイルのパス
        (tags, coverart_img):タグ、カバーアートのタプル
    """
    insert_file = OggOpus(opus_insert_file)
    
    # タグを埋め込む
    for key, value in tags.items():
        insert_file[key] = value
    
    # ファイルの上書き
    insert_file.save()
    
def convert_opus_func(file_pass):
    """
    マルチスレッド処理用の子スレッド関数
    Args:
        file_pass :  (input_file_pass, output_file_pass, wav_file_pass, jpeg_file_pass)
    """
    input_file = file_pass[0]
    output_file = file_pass[1]
    wav_file = file_pass[2]
    jpeg_file = file_pass[3]
                    
    # ファイルの種類別にタグとカバーアートを取得
    tags, coverart_img = export_coverart_img_and_tags(input_file)
    # カバーアートを中間ファイルに保存
    if coverart_img is not None:
        coverart_img.save(jpeg_file, quality=95)
    
    # インプットファイルを、メタデータとカバーアートを無視してPCM16bitに変換する
    # コンソール表示はOFFで実行
    ffmpeg_error = 0
    
    command = ["ffmpeg", "-i", input_file, wav_file, "-map_metadata", "-1", "-acodec", "pcm_s16le", "-vn"]
    try:
        subprocess.run(command, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError as e:
        ffmpeg_error = -1
        print("ffmpeg error:" + str(e))
            
    # Opusに変換する
    if ffmpeg_error == 0:
        subpro_result = subpro_opus(wav_file, output_file, bitrate, jpeg_file)
        
        # 生成した中間ファイルのWAVファイルを削除
        if os.path.exists(wav_file):
            os.remove(wav_file)
        # 生成した中間ファイルのtemp.jpegを削除
        if os.path.exists(jpeg_file):
            os.remove(jpeg_file)
        
        if re.search("success:", subpro_result):    
            insert_tags(output_file, tags)
            return subpro_result
        elif re.search("error:", subpro_result):
            return subpro_result
        else:
            print("error:conversion opus")
    
def convert_opus_mt(file_path):
    """
    convert_opus_func()をマルチスレッドで回す
    Args:
        なし
    """
    result = []
    with Pool(max_prosess_size) as pool:
        result_imap = pool.imap(func=convert_opus_func, iterable=file_path)
        for i in tqdm(result_imap, total=len(file_path), desc="ファイルの進捗："):
            result.append(i)
    return result
        
def subpro_opus(input_wav, output_opus, bitrate="96", picture_pass = None):
    """
    Wave, AIFF, FLAC, Ogg/FLAC, or raw PCM ファイルを opus ファイルに変換する関数

    Args:
        input_wav (str): 入力 wav ファイルのパス
        output_opus (str): 出力 opus ファイルのパス
        bitrate (str, optional): ビットレート. Defaults to "96".
        picture_pass : 入力カバーアートのパス
    """

    # opusenc コマンドの作成
    if os.path.exists(picture_pass):
        command = ["opusenc.exe", "--bitrate", bitrate, "--quiet", "--picture", picture_pass, input_wav, output_opus]
    else:
        command = ["opusenc.exe", "--bitrate", bitrate, "--quiet", input_wav, output_opus]

    # コマンドの実行
    try:
        subprocess.run(command, stderr=subprocess.DEVNULL, check=True)
        success_text = "success:" + str(output_opus)
        return success_text
    except subprocess.CalledProcessError as e:
        error_text = "error:" + str(output_opus) + " : " +str(e)
        return error_text

def signal_handler(sig, frame):
    exit("プログラムを強制終了します")

def main():
    
    # はじめにCtrl+Cを押したときの動作を登録しておく
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Opus変換プログラムへようこそ")
    input_check = input("入力するフォルダーを選択してください。続けるなら y を入力してください：")
    if input_check == "y":
        idir = os.path.abspath(expanduser("~"))
        input_dir_pass = Path(tkinter.filedialog.askdirectory(initialdir = idir))
        if input_dir_pass:
            output_check = input("出力するフォルダーを選択してください。続けるなら y を入力してください：")
            if output_check == "y":
                output_dir_pass = Path(tkinter.filedialog.askdirectory(initialdir = idir))
                if output_dir_pass:
                    print("Opusへの変換を開始します")
                    walk_dir_files = WalkDirAndFiles(input_dir_pass, output_dir_pass, TARGET_FILE_TYPE, DST_FILE_EXT)
                    walk_dir_files.walk_dirs(input_dir_pass)
                    walk_dir_files.walk_files(input_dir_pass)
                    walk_dir_files.make_list()
                    
                    print(f"変換するファイルの合計：{len(walk_dir_files.src_file_list)}")
                    go_check = input("本当に変換しますか？実行するなら y を入力してください：")
                    if go_check == "y":
                        walk_dir_files.make_dst_dirs()
                        log_result = convert_opus_mt(walk_dir_files.dst_file_list)
                        write_log(log_result)
                        print("すべての処理が完了しました")
                    else:
                        print("変換を中止しました")
                else:
                    print("出力フォルダーが選択されませんでした")
            else:
                print("変換を中止しました")
        else:
            print("入力フォルダーが選択されませんでした")
    else:
        print("変換を中止しました")
    
    
if __name__ == "__main__" :
    main()