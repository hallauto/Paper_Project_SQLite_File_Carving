import re
import math
from FileConnector import FileConnector
from enum import IntEnum

class JournalTypeEnum(IntEnum):
    Descriptor = 1
    Block_Commit = 2
    Journal_v1 = 3
    Journal_v2 = 4
    revocation = 5

class EXTCarving:

    EXT_J_HEADER = b'\xC0\x3B\x39\x98'
    EXT_J_SB_HEADER = b'\xC0\x3B\x39\x98\x00\x00\x00\x04'
    EXT_SUPER_B_HEADER = b'\xEF\x53\x00\x01'
    EXT_SUPER_B_HEADER_OFFSET = 56

    def __init__(self, file_connector : FileConnector=None):
        self.file_connector = file_connector
        self.journal_carver = JournalCarving(file_connector)
        self.journal_superblock_offset = -1
        self.journal_superblock_number = -1
        self.journal_superblock_content = []
        self.journal_descriptor_block_start_offset = -1 
        self.journal_descriptor_block_list = []

        self.super_b_carver = SuperBlockCarver(file_connector)
        self.superblock_offset = -1
        self.superblock_number = -1
        self.superblock_content_list = []
        self.superblock_former_offset = -1
        self.superblock_offset_list = []
        self.superblock_offset_difference_list = []

        self.group_descriptor_start = -1 
        self.group_descriptor_list = [] 
        self.group_descriptor_many = -1
        self.group_descripto_block_many = -1
        self.group_descriptor_length_list = []
        self.group_descriptor_length = -1

#SQLite카빙을 위해 저널 수퍼블록과 수퍼블록, 그룹 디스크립터 블록을 찾아서 리스트에 담는 함수입니다. 해당 정보들이 전부 모여야 SQLite 카빙이 가능합니다.

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

#수퍼블록을 찾는 함수입니다. 이 함수가 작동하기 위해서는 먼저 저널 수퍼블록을 카빙해야합니다.
    def find_superblock(self):
        rblock = b'start'
        self.file_connector.save_original_seek()
        index = 0
        while(len(rblock) > 1 and (self.file_connector.file.tell() < self.journal_superblock_offset)):  #super block은 저널 슈퍼 블록보다 전에 있습니다.
            header_offset = rblock.find(self.EXT_SUPER_B_HEADER)
            if (header_offset < 0):
                rblock = self.file_connector.block_file_read_small_to_big(index)
                index += 1
                continue
            #if (rblock[self.EXT_SUPER_B_HEADER_OFFSET:self.EXT_SUPER_B_HEADER_OFFSET + 1] is self.EXT_SUPER_B_HEADER):   조건을 조금 바꾸면 이 함수를 이용해서 슈퍼블록을 더 빠르게 찾을 수 있을것 같은데..
            self.superblock_offset = self.file_connector.file.tell() - self.file_connector.block_size
            #이렇게 되면 결국 책에서 언급한대로 처리할 수 밖에 없습니다. 이를 어떻게 처리한다...
            self.superblock_offset_list.append(self.superblock_offset)
            self.superblock_offset_difference_list.append(self.superblock_offset - self.superblock_former_offset)
            self.superblock_former_offset = self.superblock_offset
            print(str(hex(self.file_connector.file.tell() - self.file_connector.block_size)) + " 헤더 오프셋 {0}이 있습니다. 즉, 이 블록에 EXT4 슈퍼 블록이 존재합니다.".format(self.superblock_offset))
            self.superblock_number = math.ceil(self.superblock_offset / self.file_connector.block_size)
            self.superblock_content_list.append(rblock)
            self.fwrite_superblock(self.superblock_offset, len(self.superblock_content_list) - 1)
            rblock = self.file_connector.file.read(self.file_connector.block_size)

        self.file_connector.load_original_seek()

        writefile = open('super_block_offset_list.txt','w')
        for offset in self.superblock_offset_list:
            writefile.write('{0} 번째 탐지의 offset은 {1}, 이는 {2} 차이\n'.format(self.superblock_offset_list.index(offset),offset,self.superblock_offset_difference_list[self.superblock_offset_list.index(offset)]))
        writefile.close()

#수퍼블록과 저널 수퍼블록을 파일로 출력시키는 함수입니다.
    def fwrite_superblock(self, superblock_offset = 0, superblock_content_list_index = 0):
        writefile = open('super_block_offset_{0}'.format(superblock_offset),'wb')
        writefile.write(bytes(self.superblock_content_list[superblock_content_list_index]))
        writefile.close()

    def fwrite_journal_superblock(self):
        writefile = open('journal_super_block', 'wb')
        writefile.write(bytes(self.journal_superblock_content))
        writefile.close()

#발견한 저널 수퍼블록과 수퍼블록, 그룹 디스크립터 블록을 파싱해서 필요한 데이터를 얻는 함수입니다.
    def parsing_super_block(self, superblock_content_list_index):
        content = self.superblock_content_list[superblock_content_list_index]
        offset = self.superblock_offset_list[superblock_content_list_index] % self.file_connector.block_size

        self.group_descriptor_many = math.ceil(int(content[offset + 0x4:offset + 0x8]) / int(content[offset + 0x20:offset + 0x24]))
        self.group_descripto_block_many = int.from_bytes(content[offset + 0x20:offset + 0x24],'big')

    #def parsing_group_descriptor(self, group_descriptor_list_index):




class JournalCarving:

    def __init__(self, file_connector : FileConnector=None):
        self.file_connector = file_connector
        self.journal_start_block = 0
        self.transaction_number = 0

        self.journal_sequence = 0
        self.journal_type = 0
        self.journal_type_name = ""
        self.journal_results = []

    def find_superblock(self):
        rblock = 'start'
        while(len(rblock) > 1):
            header_offset = rblock.find(self.EXT_J_HEADER)

class SuperBlockCarver:


    def __init__(self, file_connector : FileConnector=None):
        self.file_connetor = file_connector
        self.superblock_offset = -1 
        self.superblock_content = [] 
        self.group_descriptor_start = -1 
        self.group_descriptor_list = [] 
        self.group_descriptor_many = -1 
        self.group_descriptor_length_list = [] 
        self.group_descriptor_length = -1 




