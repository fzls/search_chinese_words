import json
import os
import re
from typing import Iterator, List, Set, Tuple
from collections import Counter

import jieba

from log import logger

ENABLE_PADDLE = True
# ENABLE_PADDLE = False

ENABLE_CACHE = True
# ENABLE_CACHE = False

if ENABLE_PADDLE:
    jieba.enable_paddle()
jieba.initialize()

cache_file_suffix = "cache.搜索后缀.json"
cache_file_filepath = "cache.搜索路径.json"
cache_file_valid_filepath = "cache.有效路径.json"
cache_file_sentences = "cache.连续中文.json"
cache_file_raw_sentences = "cache.连续中文.txt"
cache_file_sentences_debug_with_path = "cache.连续中文-调试版本.json"
cache_file_words = "cache.分词.json"
cache_file_words_dict = {
    True: "cache.words.paddle.json",
    False: "cache.words.no_paddle.json",
}
cache_file_statistics = "cache.统计信息.json"

re_chinese_words = re.compile('([\u4e00-\u9fa5]+)+?')

possiable_encodings = [
    "utf-8",
    "gbk",
    "utf-16",
    "gb2312",
]

ignored_dirs = {
    ".",
    "..",
    ".svn",
    ".git",
    ".vs",
    "3rdparty",
    "3rd",
    "AnimationFBX",
    ".localhistory",
    "go",
    "ResourceCheckConfig",
    "AssetPreloadData",
    "LogicSceneConfig",
    "MapGuide",
    "LogicMap",
    "StreamingAssetOptimizer",
    "GameDesignerTools",
    "测试用例",
    "Tools",
    "Test",
    "tsssdk_server",
    "Library",
    "documents",
    "UnityPlugin",
    "ForBuild",
    "PendantOffsetResource",
    "SimpleAnimationData",
}
ignored_files = {
    "E:\\JX3M\\src\\trunk\\JX3Pocket\\Assets\\JX3Game\\Source\\File\\Item\\Item_value.xls",
    "E:\\JX3M\\src\\trunk\\JX3Pocket\\Assets\\JX3Game\\Source\\File\\UI\\UITongActivityTab.xls",
    "E:\\JX3M\\src\\trunk\\JX3Pocket\\Assets\\JX3Game\\Source\\File\\ServerList.xls",
}
target_suffixes = {
    '.json',
    # '.txt',
    '.lua',
    '.go',
    # '.cs',
    '.xls',
    '.tab',
}


def save_cache(ctx: str, content: any, cache_path: str):
    with open(cache_path, "w", encoding='utf-8') as f:
        logger.info(f"写入缓存文件：{ctx} {cache_path}")
        json.dump(content, f, ensure_ascii=False, indent=2)


def load_cache(ctx: str, cache_path: str) -> any:
    logger.info(f"使用缓存文件：{ctx} {cache_path}")
    with open(cache_path, "r", encoding='utf-8') as f:
        return json.load(f)


def extract_chinese_sentences_in_file(filepath: str) -> List[str]:
    sentences: List[str] = []

    for encoding in possiable_encodings:
        try:
            with open(filepath, "r", encoding=encoding) as f:
                for line in f:
                    m = re_chinese_words.findall(line)  # 使用正则表达获取中文
                    if m:
                        sentences.extend(m)

            # print('|'.join(sentences))
            # print(len(sentences))
            # print(len(set(sentences)))
            return sentences
        except:
            pass

    raise Exception("Can't decode file: " + filepath)


def extract_chinese_words_in_dir(dirpath: str, split_words=False) -> List[str]:
    # 获取目标文件
    logger.info(f"开始解析目录：{dirpath}, 将尝试以下后缀名的文件：{target_suffixes}")

    target_files: List[str]

    use_cache = True
    # use_cache = False
    use_cache = use_cache and ENABLE_CACHE
    if use_cache and os.path.exists(cache_file_filepath):
        logger.info(f"使用缓存文件：{cache_file_filepath}")
        target_files = load_cache("目标文件路径", cache_file_filepath)
        # with open(cache_file_filepath, "r") as f:
        #     target_files = json.load(f)
    else:
        logger.info(f"未启用缓存({use_cache})或者缓存不存在，重新生成缓存文件")
        target_files = list(recursive_get_filepath_of(dirpath, target_suffixes))
        save_cache("目标文件路径", target_files, cache_file_filepath)
        save_cache("搜索后缀", list(target_suffixes), cache_file_suffix)

    logger.info(f"解析结束，共解析到{len(target_files)}个文件")

    # 统计文件中包含的中文句子
    sentences: Set[str] = set()
    sentences_debug_with_path: List[Tuple[str, str]] = []
    valid_target_files: List[str] = []

    use_cache = True
    # use_cache = False
    use_cache = use_cache and ENABLE_CACHE
    logger.info("开始统计中文句子")
    if use_cache and os.path.exists(cache_file_sentences):
        sentences = set(load_cache("中文句子", cache_file_sentences))
        valid_target_files = load_cache("有效路径", cache_file_valid_filepath)
    else:
        for idx, filepath in enumerate(target_files):
            print(f"\r[{idx + 1}/{len(target_files)}]: {filepath}", end='', flush=True)

            if filepath in ignored_files:
                continue

            new_sentences = extract_chinese_sentences_in_file(filepath)
            if len(new_sentences) == 0:
                continue

            for s in new_sentences:
                if s in sentences:
                    continue
                sentences.add(s)
                sentences_debug_with_path.append((s, filepath))
            valid_target_files.append(filepath)
        print()
        save_cache("中文句子", sorted(list(sentences)), cache_file_sentences)
        save_cache("中文句子-调试版本", sorted(list(sentences_debug_with_path)), cache_file_sentences_debug_with_path)
        save_cache("有效路径", valid_target_files, cache_file_valid_filepath)

    logger.info(f"中文句子统计完成，共计{len(sentences)}个，此外，有效路径为 {len(valid_target_files)} 个")

    # 分词
    words: Set[str] = set()
    if split_words:
        use_cache = True
        # use_cache = False
        use_cache = use_cache and ENABLE_CACHE
        logger.info("开始分词")
        if use_cache and os.path.exists(cache_file_words):
            words = set(load_cache("中文分词", cache_file_words))
        else:
            for idx, word in enumerate(sentences):
                print(f"\r[{idx + 1}/{len(sentences)}]: {word[:6]}", end='', flush=True)
                words.update(jieba.cut(word))
            print()
            save_cache("中文分词", sorted(list(words)), cache_file_words)
            save_cache(f"中文分词-{ENABLE_PADDLE}", sorted(list(words)), cache_file_words_dict[ENABLE_PADDLE])

        logger.info(f"分词完成，共计{len(words)}个")
    else:
        words = sentences

    logger.info(f"开始统计字数信息")
    counter = Counter()

    counter["中文句子-句数"] = len(sentences)
    for sentence in sentences:
        counter["中文句子-字数"] += len(sentence)

    counter["中文分词-词数"] = len(words)
    for word in words:
        counter["分词后-字数"] += len(word)

    counter["搜索的文件数"] = len(target_files)
    counter["包含中文的文件数"] = len(valid_target_files)

    save_cache("统计信息", counter, cache_file_statistics)

    # print('|'.join(words))
    return list(words)


def recursive_get_filepath_of(dirpath: str, target_suffixes: Set[str]) -> Iterator[str]:
    with os.scandir(dirpath) as it:
        for entry in it:
            entry: os.DirEntry
            if entry.name in ignored_dirs:
                continue

            if entry.is_dir():
                yield from recursive_get_filepath_of(entry.path, target_suffixes)
            elif entry.is_file():
                suffix = os.path.splitext(entry.name)[1]
                if suffix in target_suffixes:
                    print(entry.path)
                    yield entry.path


if __name__ == '__main__':
    dirpath = "E:\\JX3M\\src\\trunk"

    extract_chinese_words_in_dir(dirpath, split_words=True)
