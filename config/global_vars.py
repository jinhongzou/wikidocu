import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

WIKIDOCU_QA_DIR = os.getenv("WIKIDOCU_QA_DIR", ".QADocs")

# 检查目录是否存在，不存在则创建
if not os.path.exists(WIKIDOCU_QA_DIR):
    os.makedirs(WIKIDOCU_QA_DIR)

LOG_LVL=False
LOG_FILE="logs/app_wikidocu.log"

# from src.filehandler import FileHandler
# UI_DETAIL_OUTPUT_PATH = 'respone_out/ui_detail_output.txt'
# UI_MAIN_OUTPUTT_PATH= 'respone_out/ui_main_output.txt'
# ui_detail_output_handler= FileHandler(UI_DETAIL_OUTPUT_PATH)
# ui_main_outputt_handler= FileHandler(UI_MAIN_OUTPUTT_PATH)

