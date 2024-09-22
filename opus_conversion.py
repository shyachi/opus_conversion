# このプログラムは入力の音楽ファイルのディレクトリー構成を保ったまま
# opusファイルに変換するプログラムです
# 別途必要な実行ファイル
# opusenc.exe : opusファイルを作成するのに必要です
# ffmpeg.exe : 様々な音楽ファイルをwavに変換し、opusenc.exeに渡すために必要です

import os
from os.path import expanduser
import subprocess
import ffmpeg
from tqdm import tqdm
import tkinter
from tkinter import filedialog
import concurrent.futures

# タグとカバーアート用のライブラリ群
from io import BytesIO
from PIL import Image
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from mutagen.oggopus import OggOpus


TARGET_FILE_TYPE = [".flac",".mp3"]
OPUS_EXT = ".opus"
WAV_EXT = ".wav"
JPEG_EXT = ".jpg"

# 入力するディレクトリーのパスと、その上のディレクトリーの名前を取得
input_dir_pass = ""
input_dir_root_pass = os.path.abspath(os.path.dirname(input_dir_pass))
# 出力するディレクトリーのパスと、その上のディレクトリーの名前を取得
output_dir_pass = ""
output_dir_root_pass = os.path.abspath(os.path.dirname(output_dir_pass))

# ファイルパスのリスト
# (input_file_pass, output_file_pass, wav_file_pass, jpeg_file_pass)のタプルを入れる
file_pass_list = []

# Opusビットレート指定
bitrate = "96"

# マルチスレッド数指定
max_thread = os.cpu_count() // 2

def copy_directory(src, dst):
    # この関数は、元のディレクトリー構造をコピー先に作り出します
    # src:コピー元のディレクトリーのパス
    # dst:コピー先のディレクトリーのパス
    
    os.makedirs(dst, exist_ok=True)
    
    # ディレクトリー構造をコピー
    # もしすでにディレクトリーが存在したら、そのまま上書き
    for root, dirs, files in os.walk(src):
        for dir in dirs:
            src_dir = os.path.join(root, dir)       # 入力のディレクトリー構造のパス
            dst_dir = src_dir.replace(src, dst)     # 出力のディレクトリー構造のパス
            os.makedirs(dst_dir, exist_ok=True)
            
        # ファイルが見つかった階層で、ターゲットファイルがあるかどうかチェック
        if len(files) > 0:
            target_file_check(src_dir, dst_dir)
            
def target_file_check(src_dir, dst_dir):    
    # src_dirに存在する音楽ファイルのチェック
    for root, dirs, files in os.walk(src_dir):
        for input_file in files:
            filename, ext = os.path.splitext(input_file)
            if ext in TARGET_FILE_TYPE:
                # もしターゲットの拡張子と一致したら
                # 入力パスと出力パスのリストに追加
                output_file = filename + str(OPUS_EXT)
                wav_file = filename + str(WAV_EXT)
                jpeg_file = filename + str(JPEG_EXT)
                
                abs_input_pass = os.path.join(input_dir_root_pass, os.path.join(src_dir, input_file))
                abs_output_pass = os.path.join(output_dir_root_pass, os.path.join(dst_dir, output_file))
                abs_wav_pass = os.path.join(output_dir_root_pass, os.path.join(dst_dir, wav_file))
                abs_jpeg_pass = os.path.join(output_dir_root_pass, os.path.join(dst_dir, jpeg_file))
                
                file_pass_list.append((abs_input_pass, abs_output_pass, abs_wav_pass, abs_jpeg_pass))

def file_pass_check():
    """
    ファイルパスのチェック用関数
    Args:
    """
    for list in file_pass_list:
        print(f"input file pass:{list[0]}")
        print(f"output file pass:{list[1]}")
        print(f"wav file pass:{list[2]}")
        print(f"jpeg file pass:{list[3]}")
        
def export_coverart_img_and_tags(input_file_pass):
    """
    入力ファイルのカバーアートとタグを抽出して返す関数
    出力はtags(辞書形式)とカバーアートのタプル
    Args:
        input_file_pass (str): 入力ファイルのパス
    """
    filename, ext = os.path.splitext(input_file_pass)
    coverart_img = None
    
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
    ffmpeg.input(input_file).output(wav_file, map_metadata='-1', acodec='pcm_s16le', vn=None).run(quiet=True)
    
    # Opusに変換する
    subpro_opus(wav_file, output_file, bitrate, jpeg_file)
    
    # 生成した中間ファイルのWAVファイルを削除
    if os.path.exists(wav_file):
        os.remove(wav_file)
    # 生成した中間ファイルのtemp.jpegを削除
    if os.path.exists(jpeg_file):
        os.remove(jpeg_file)
        
    insert_tags(output_file, tags)
        
    
def convert_opus_mt():
    """
    convert_opus_func()をマルチスレッドで回す
    Args:
        なし
    """
    
    tasks = file_pass_list
    # 指定のスレッド数のスレッドプールを作成する
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_thread) as executor:
        # 進捗管理のためtqdmでexecutor.mapの戻り値をラップ
        # 進捗バーの表示更新のために、空のfor分を回す
        for _ in tqdm(executor.map(convert_opus_func, tasks), total=len(tasks), desc="ファイルの進捗状況"):
            pass
        
        
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
    except subprocess.CalledProcessError as e:
        print(f"エラーが発生しました: {e}")

def main():
    print("Opus変換プログラムへようこそ")
    input_check = input("入力するフォルダーを選択してください。続けるなら y を入力してください：")
    if input_check == "y":
        idir = os.path.abspath(expanduser("~"))
        input_dir_pass = tkinter.filedialog.askdirectory(initialdir = idir)
        if input_dir_pass:
            output_check = input("出力するフォルダーを選択してください。続けるなら y を入力してください：")
            if output_check == "y":
                output_dir_pass = tkinter.filedialog.askdirectory(initialdir = idir)
                if output_dir_pass:
                    print("Opusへの変換を開始します")
                    copy_directory(input_dir_pass, output_dir_pass)
                    print(f"変換するファイルの合計：{len(file_pass_list)}")
                    go_check = input("本当に変換しますか？実行するなら y を入力してください：")
                    if go_check == "y":
                        # file_pass_check()
                        convert_opus_mt()
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