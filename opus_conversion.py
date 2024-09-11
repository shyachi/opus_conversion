# このプログラムは入力の音楽ファイルのディレクトリー構成を保ったまま
# opusファイルに変換するプログラムです
# 別途必要な実行ファイル
# opusenc.exe : opusファイルを作成するのに必要です
# ffmpeg.exe : 様々な音楽ファイルをwavに変換し、opusenc.exeに渡すために必要です

import os
import ffmpeg
from mutagen.flac import FLAC

# 入力するディレクトリーのパスと、その上のディレクトリーの名前を取得
INPUT_DIR_PASS = "music_input"
INPUT_DIR_ROOT_PASS = os.path.abspath(os.path.dirname(INPUT_DIR_PASS))
# 出力するディレクトリーのパスと、その上のディレクトリーの名前を取得
OUTPUT_DIR_PASS = "music_output"
OUTPUT_DIR_ROOT_PASS = os.path.abspath(os.path.dirname(OUTPUT_DIR_PASS))

TARGET_FILE_TYPE = [".flac",".wav","mp3",".ogg",".aac",".wma"]
INPUT_FILE_PASS_LIST = []
OUTPUT_FILE_PASS_LIST = []
OPUS_EXT = ".opus"

def copy_directory(src, dst):
    # この関数は、元のディレクトリー構造をコピー先に再帰的に作り出します
    # src:コピー元のディレクトリーのパス
    # dst:コピー先のディレクトリーのパス
    
    os.makedirs(dst, exist_ok=True)
    
    # 再帰的にディレクトリーをコピー
    # もしすでにディレクトリーが存在したら、そのまま上書き
    for root, dirs, files in os.walk(src):
        for dir in dirs:
            src_dir = os.path.join(root, dir)       # 入力のディレクトリー構造のパス
            dst_dir = src_dir.replace(src, dst)     # 出力のディレクトリー構造のパス
            os.makedirs(dst_dir, exist_ok=True)
            target_file_check(src_dir, dst_dir)
            
    file_pass_check()
            
def target_file_check(src_dir, dst_dir):
    # 将来的に、ここでファイル変換をします
    print(f"現在のディレクトリー構造:{src_dir}")
    
    # src_dirに存在する音楽ファイルのチェック
    for root, dirs, files in os.walk(src_dir):
        for input_file in files:
            filename, ext = os.path.splitext(input_file)
            if ext in TARGET_FILE_TYPE:
                # もしターゲットの拡張子と一致したら
                # 入力パスと出力パスのリストに追加
                output_file = filename + str(OPUS_EXT)
                
                current_input_pass = os.path.join(src_dir, input_file)
                current_output_pass = os.path.join(dst_dir, output_file)
                
                INPUT_FILE_PASS_LIST.append(os.path.join(INPUT_DIR_ROOT_PASS, current_input_pass))
                OUTPUT_FILE_PASS_LIST.append(os.path.join(OUTPUT_DIR_ROOT_PASS, current_output_pass))
            else:
                # print(f"ターゲットではないファイル：{filename} 拡張子：{ext}")
                break

def file_pass_check():
    # 入力のターゲットのファイルパス一覧
    for input_file_pass in INPUT_FILE_PASS_LIST:
        print(f"input file pass:{input_file_pass}")
        
    # 出力のファイル名とパス一覧
    for output_file_pass in OUTPUT_FILE_PASS_LIST:
        print(f"output file pass:{output_file_pass}")
        
    # 入力ファイルのInfo
    #for input_file_pass in INPUT_FILE_PASS_LIST:
    #    music_info = ffmpeg.probe(input_file_pass)
    #    print(music_info)
        
    music_info = ffmpeg.probe(r"C:\Users\mspsh\Documents\Python\opus_conversion\music_input\ACIDMAN\創\01_8to1 completed.flac")
    print(music_info)
    
    audio = FLAC(r"C:\Users\mspsh\Documents\Python\opus_conversion\music_input\ACIDMAN\創\01_8to1 completed.flac")
    print(audio.tags)
    
    
def main():
    copy_directory(INPUT_DIR_PASS, OUTPUT_DIR_PASS)
    
if __name__ == "__main__" :
    main()