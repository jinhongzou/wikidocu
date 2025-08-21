import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

from src.filehandler import FileHandler

UI_DETAIL_OUTPUT_PATH = 'respone_out/ui_detail_output.txt'
UI_MAIN_OUTPUTT_PATH= 'respone_out/ui_main_output.txt'
WIKIDOCU_QA_DIR = os.getenv("WIKIDOCU_QA_DIR", ".QADocs")

# ui_detail_output_handler= FileHandler(UI_DETAIL_OUTPUT_PATH)
# ui_main_outputt_handler= FileHandler(UI_MAIN_OUTPUTT_PATH)

