# -*- coding: utf-8 -*-
import pandas as pd
from openai import OpenAI, RateLimitError, APIError
import os
from dotenv import load_dotenv
import logging
import time
import re

# --- 配置 ---
load_dotenv()  # 加载 .env 文件中的环境变量
INPUT_FILENAME = "example.xlsx"
OUTPUT_FILENAME = "medical_info_translated.csv"
# 从 COMMAND.md 假设的列名，如果实际文件不同，需要修改这里
ENGLISH_NAME_COL = "Drug_Name"
ENGLISH_TYPE_COL = "Reason"
ENGLISH_DESC_COL = "Description"
CHINESE_NAME_COL = "药品名称（中文）"
CHINESE_TYPE_COL = "药瓶类型（中文）"
CHINESE_DESC_COL = "药品描述（中文）"

# OpenRouter API 配置
API_KEY = os.getenv("OPENROUTER_API_KEY")
# 可选：从 .env 获取站点信息
SITE_URL = os.getenv("YOUR_SITE_URL", None) # 提供默认值
SITE_NAME = os.getenv("YOUR_SITE_NAME", None) # 提供默认值
MODEL_NAME = "google/gemini-flash-1.5-8b" # 使用 COMMAND.md 中指定的模型

# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- OpenAI 客户端初始化 ---
if not API_KEY:
    logging.error("错误：未找到 OPENROUTER_API_KEY。请确保 .env 文件存在且包含您的 API 密钥。")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

# --- 翻译函数 ---
def translate_text(name_en, type_en, desc_en, retry_count=3, delay=5):
    """
    调用 OpenRouter API 翻译医药信息。

    Args:
        name_en (str): 英文药品名称.
        type_en (str): 英文药瓶类型.
        desc_en (str): 英文药品描述.
        retry_count (int): 失败重试次数.
        delay (int): 重试前的延迟秒数.

    Returns:
        tuple: (中文名称, 中文类型, 中文描述) 或 (None, None, None) 如果失败.
    """
    prompt = f"""你是一名专业的医药翻译AI，请严格按照以下规则执行：

1. **翻译规范**
   - 使用简体中文
   - 遵循中国药典术语标准
   - 保持专业性和准确性

2. **输入格式**
   待翻译内容将按以下格式提供：
待翻译内容：
药品名称: {name_en}
药瓶类型: {type_en}
药品描述: {desc_en}

3. **输出格式**
- 必须用 `||` 分隔三个部分
- 格式：`中文药品名称 || 中文药瓶类型 || 中文药品描述`
- 不可以出现表头
- 禁止换行/分段
- 禁止省略分隔符

4. **特殊处理**
- 若药品名称含多个变体（如不同浓度），合并为一个连续字符串
- 浓度单位保留数字格式（如0.05%）
- 剂型统一译为"凝胶"/"片剂"等标准术语
- 规格单位转换为"克"/"毫升"等法定计量单位

5. **例如**
药品名称: A Ret 0.05% Gel 20gmA Ret 0.1% Gel 20gmA Ret 0.025% Gel 20gm
药瓶类型: Acne
药品描述: A RET 0.025% is a prescription medicine that is used to reduce fine wrinkles

你返回的结果应当为:

维A酸 0.05% 凝胶 20克 维A酸 0.1% 凝胶 20克 维A酸 0.025% 凝胶 20克 || 痤疮治疗用 || 维A酸0.025%凝胶为处方药物，适用于改善细纹

6. **错误处理**
- 如遇无法翻译的内容，保留英文原词并标注[待确认]
- 禁止虚构信息
"""

    for attempt in range(retry_count):
        try:
            logging.debug(f"尝试翻译: 名称='{name_en}', 类型='{type_en}' (尝试 {attempt + 1}/{retry_count})")
            completion = client.chat.completions.create(
                extra_body={},
                model="google/gemini-flash-1.5-8b",
                messages=[
                   {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                top_p=0.9,       # 控制生成多样性的另一种方式
                frequency_penalty=0.1,  # 降低重复内容
                presence_penalty=0.1,   # 鼓励使用不同词汇
                timeout=30  # 显式设置超时
            )
            response_text = completion.choices[0].message.content.strip()
            logging.debug(f"API 原始响应: {response_text}")

            # 解析响应
            parts = response_text.split('||')
            if len(parts) == 3:
                name_zh = parts[0].strip()
                type_zh = parts[1].strip()
                desc_zh = parts[2].strip()
                logging.debug(f"成功解析: 名称='{name_zh}', 类型='{type_zh}'")
                return name_zh, type_zh, desc_zh
            else:
                # print(parts)
                logging.warning(f"无法按预期格式解析 API 响应: '{response_text}'. 尝试直接使用响应。")
                name_zh = parts[-3].strip()
                type_zh = parts[-2].strip()
                desc_zh = parts[-1].strip()
                # 尝试作为一种回退机制，如果格式不完全匹配但内容可能有用
                # 这里可以根据需要添加更复杂的解析逻辑
                # 为简单起见，如果格式不对，我们认为翻译失败
                # logging.error(f"解析失败，响应未使用 '||' 分隔成三部分: {response_text}")
                return None, None, None # 或者可以尝试返回 response_text 本身给某一列

        except RateLimitError as e:
            logging.warning(f"API 速率限制错误: {e}. 等待 {delay * (attempt + 1)} 秒后重试...")
            time.sleep(delay * (attempt + 1))
        except APIError as e:
            logging.error(f"API 调用失败 (尝试 {attempt + 1}/{retry_count}): {e}")
            if attempt == retry_count - 1:
                logging.error("已达到最大重试次数，翻译失败。")
                return None, None, None
            time.sleep(delay)
        except Exception as e:
            logging.error(f"翻译过程中发生未知错误 (尝试 {attempt + 1}/{retry_count}): {e}")
            if attempt == retry_count - 1:
                return None, None, None
            time.sleep(delay)

    return None, None, None # 所有重试失败

# --- 主逻辑 ---
def main():
    logging.info(f"开始处理文件: {INPUT_FILENAME}")

    try:
        # 读取 Excel 文件，需要安装 openpyxl
        df = pd.read_excel(INPUT_FILENAME)
        logging.info(f"成功读取文件，共 {len(df)} 行数据。")
    except FileNotFoundError:
        logging.error(f"错误：输入文件 '{INPUT_FILENAME}' 未找到。")
        return
    except Exception as e:
        logging.error(f"读取 Excel 文件时出错: {e}")
        return

    # 检查所需列是否存在
    required_cols = [ENGLISH_NAME_COL, ENGLISH_TYPE_COL, ENGLISH_DESC_COL]
    if not all(col in df.columns for col in required_cols):
        logging.error(f"错误：输入文件缺少必要的列。需要: {required_cols}, 实际列: {list(df.columns)}")
        return

    # 初始化新列
    df[CHINESE_NAME_COL] = ""
    df[CHINESE_TYPE_COL] = ""
    df[CHINESE_DESC_COL] = ""

    # 逐行翻译
    for index, row in df.iterrows():
        name_en = str(row[ENGLISH_NAME_COL]) if pd.notna(row[ENGLISH_NAME_COL]) else ""
        type_en = str(row[ENGLISH_TYPE_COL]) if pd.notna(row[ENGLISH_TYPE_COL]) else ""
        desc_en = str(row[ENGLISH_DESC_COL]) if pd.notna(row[ENGLISH_DESC_COL]) else ""

        # 如果所有待翻译字段都为空，则跳过
        if not name_en and not type_en and not desc_en:
            logging.info(f"跳过第 {index + 1} 行，因为所有英文列都为空。")
            continue

        logging.info(f"正在翻译第 {index + 1}/{len(df)} 行...")
        name_zh, type_zh, desc_zh = translate_text(name_en, type_en, desc_en)

        if name_zh is not None:
            df.loc[index, CHINESE_NAME_COL] = name_zh
            df.loc[index, CHINESE_TYPE_COL] = type_zh
            df.loc[index, CHINESE_DESC_COL] = desc_zh
            logging.info(f"第 {index + 1} 行翻译完成。")
        else:
            logging.error(f"第 {index + 1} 行翻译失败。")
            # 保留空值或标记为失败
            df.loc[index, CHINESE_NAME_COL] = "翻译失败"
            df.loc[index, CHINESE_TYPE_COL] = "翻译失败"
            df.loc[index, CHINESE_DESC_COL] = "翻译失败"

        # 在每次 API 调用后稍作停顿，避免过于频繁请求
        time.sleep(1) # 暂停 1 秒

    # 保存结果到 CSV
    try:
        df.to_csv(OUTPUT_FILENAME, index=False, encoding='utf-8-sig') # 使用 utf-8-sig 确保 Excel 正确显示中文
        logging.info(f"翻译完成，结果已保存到 {OUTPUT_FILENAME}")
    except Exception as e:
        logging.error(f"保存 CSV 文件时出错: {e}")

if __name__ == "__main__":
    main()