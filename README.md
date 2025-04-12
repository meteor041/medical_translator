# 医药信息翻译器 (Medic Translator)

本项目包含一个 Python 脚本，用于读取包含医药信息的 Excel 文件 (`.xlsx`)，利用 OpenRouter API 将指定的英文列（药品名称、药瓶类型、药品描述）翻译成中文，并将翻译结果保存到一个新的 CSV 文件中。

## 功能特性

*   从 Excel 文件 (`.xlsx`) 读取数据。
*   调用 OpenRouter API (默认为 `openai/gpt-4o-mini-search-preview` 模型) 进行翻译。
*   翻译特定的列：药品名称、药瓶类型、药品描述。
*   将原始数据和翻译后的中文结果保存到新的 CSV 文件 (`.csv`)。
*   使用 `.env` 文件安全地管理 API 密钥。
*   提供日志记录以跟踪脚本执行过程。
*   包含基本的错误处理和重试机制。

## 先决条件

*   Python 3.7 或更高版本
*   pip (Python 包安装器)

## 安装与设置

1.  **获取代码**:
    *   如果您使用 Git，请克隆仓库：
        ```bash
        git clone <repository_url>
        cd medic_translator
        ```
    *   或者，直接下载项目文件 (`translate_medicine.py`, `requirements.txt`, `.env.example`, `Medicine_description.xlsx`) 到一个目录中。

2.  **配置 API 密钥**:
    *   将项目根目录下的 `.env.example` 文件复制并重命名为 `.env`。
    *   编辑 `.env` 文件，将 `YOUR_OPENROUTER_API_KEY_HERE` 替换为您真实的 OpenRouter API 密钥。
    *   (可选) 您也可以在 `.env` 文件中设置 `YOUR_SITE_URL` 和 `YOUR_SITE_NAME`，这有助于在 OpenRouter 上进行排名。

3.  **安装依赖**:
    打开终端 (或 PowerShell)，导航到项目目录，然后运行以下命令安装所需的 Python 库：
    ```bash
    pip install -r requirements.txt
    ```

## 使用方法

1.  **准备输入文件**:
    *   确保项目根目录下存在名为 `Medicine_description.xlsx` 的 Excel 文件。
    *   该文件应至少包含以下列（列名需与脚本中的配置匹配）：
        *   `药品名称（英文）`
        *   `药瓶类型（英文）`
        *   `药品描述（英文）`

2.  **运行脚本**:
    在终端中，确保您位于项目目录下，然后执行脚本：
    ```bash
    python translate_medicine.py
    ```

3.  **查看输出**:
    *   脚本执行时会在终端显示进度日志。
    *   执行完成后，会在项目根目录下生成一个名为 `medical_info_translated.csv` 的文件。该文件将包含原始的英文列以及新增的中文翻译列：
        *   `药品名称（中文）`
        *   `药瓶类型（中文）`
        *   `药品描述（中文）`

## 配置文件 (`translate_medicine.py`)

脚本顶部包含一些可配置的变量：

*   `INPUT_FILENAME`: 输入的 Excel 文件名 (默认为 `"Medicine_description.xlsx"`)。
*   `OUTPUT_FILENAME`: 输出的 CSV 文件名 (默认为 `"medical_info_translated.csv"`)。
*   `ENGLISH_NAME_COL`, `ENGLISH_TYPE_COL`, `ENGLISH_DESC_COL`: 输入文件中需要翻译的英文列名。
*   `CHINESE_NAME_COL`, `CHINESE_TYPE_COL`, `CHINESE_DESC_COL`: 输出文件中新增的中文列名。
*   `MODEL_NAME`: 用于翻译的 OpenRouter 模型 (默认为 `"openai/gpt-4o-mini-search-preview"`)。

## 依赖库

*   [pandas](https://pandas.pydata.org/): 用于数据处理，读取 Excel 和写入 CSV。
*   [openai](https://github.com/openai/openai-python): 用于与 OpenRouter API 进行交互。
*   [python-dotenv](https://github.com/theskumar/python-dotenv): 用于从 `.env` 文件加载环境变量 (API 密钥)。
*   [openpyxl](https://openpyxl.readthedocs.io/en/stable/): `pandas` 读取 `.xlsx` 文件所需的库。