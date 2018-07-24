import re
import math
from FileConnector import FileConnector
from enum import IntEnum
from ExTCarving import EXTCarving


class JournalCarving:
    def __init__(self, file_connector : FileConnector=None):
        self.file_connector = file_connector
        self.journal_carver = JournalCarving(file_connector)
        self.journal_superblock_offset = -1
        self.journal_superblock_number_list = -1
        self.journal_superblock_content = []
        self.journal_descriptor_block_start_offset = -1
        self.journal_descriptor_block_list = []

#저널 수퍼블록을 카빙하는 함수입니다.
    def find_journal_superblock(self):
        rblock = b'start'
        self.file_connector.save_original_seek()
        while(len(rblock) > 1):
            header_offset = rblock.find(self.EXT_J_SB_HEADER)
            if (header_offset < 0):
                rblock = self.file_connector.file.read(self.file_connector.block_size)
                continue
            print(str(hex(self.file_connector.file.tell() - self.file_connector.block_size)) + " 헤더 오프셋 {0}이 있습니다. 즉, 이 블록에 EXT4 저널 슈퍼 블록이 존재합니다.".format(header_offset))
            self.journal_superblock_offset = self.file_connector.file.tell() - self.file_connector.block_size
            self.journal_superblock_number = math.ceil(self.journal_superblock_offset / self.file_connector.block_size)
            self.journal_superblock_content = rblock
            self.fwrite_journal_superblock()
            break

        self.file_connector.load_original_seek()