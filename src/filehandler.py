import os
import logging

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self, file_path):
        """
        初始化 FileHandler 对象。
        
        参数:
            file_path (str): 文件的路径。
        """
        self.file_path = file_path
        # 自动创建父级目录（如果不存在）
        self._ensure_directory_exists()
        self._turns = 0


    def _ensure_directory_exists(self):
        """
        确保文件所在目录存在，不存在则创建。
        """
        directory = os.path.dirname(self.file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            logger.info("已创建目录: %s", directory)

    def write_content(self, content):
        """
        将内容写入文件（追加模式）。
        
        参数:
            content (str): 要写入文件的内容。
        """

        try:
            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(content + '\n')
            #print(f"✅ 内容已写入文件 '{self.file_path}'。")
        except Exception as e:
            logger.error("写入文件时出错: %s", e)

    def clear_file(self):
        """
        清空文件内容。
        """
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.truncate()
            logger.info("文件 '%s' 已清空。", self.file_path)
        except Exception as e:
            logger.error("清空文件时出错: %s", e)


if __name__ == '__main__':
    file_path = '.frontend/ui_detail_output.txt'
    handler = FileHandler(file_path)

    handler.clear_file()
    handler.write_content("这是写入到 .frontend/ui_detail_output.txt 的内容。")