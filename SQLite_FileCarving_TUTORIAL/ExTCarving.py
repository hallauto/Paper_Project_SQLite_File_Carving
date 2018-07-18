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
    EXT_SUPER_B_HEADER = b'\x53\xEF\x01\x00'
    EXT_SUPER_B_HEADER_OFFSET = 56

    def __init__(self, file_connector : FileConnector=None):
        self.file_connector = file_connector
        self.journal_carver = JournalCarving(file_connector)
        self.journal_superblock_offset = -1
        self.journal_superblock_number_list = -1
        self.journal_superblock_content = []
        self.journal_descriptor_block_start_offset = -1 
        self.journal_descriptor_block_list = []

        self.super_b_carver = SuperBlockCarver(file_connector)
        self.superblock_number_list = []
        self.superblock_content_list = []
        self.superblock_former_offset = -1
        self.superblock_offset_list = []
        self.superblock_offset_difference_list = []

        self.group_descriptor_start = -1 
        self.group_descriptor_content_list = [[[]]]
        self.group_descriptor_many_list = []
        self.group_descriptor_block_many_list = []
        self.group_descriptor_inode_many_list = []
        self.group_descriptor_length_list = []

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
            rblock = self.file_connector.block_file_read(index)
            header_offset = rblock.find(self.EXT_SUPER_B_HEADER)
            if (header_offset < 0):
                index+=1
                continue
            superblock_offset = self.file_connector.file.tell() - self.file_connector.block_size + header_offset - self.EXT_SUPER_B_HEADER_OFFSET
            self.superblock_offset_list.append(superblock_offset)
            self.superblock_offset_difference_list.append(superblock_offset - self.superblock_former_offset)
            self.superblock_former_offset = superblock_offset
            print(str(hex(self.file_connector.file.tell() - self.file_connector.block_size)) + " 헤더 오프셋 {0}({1})이 있습니다. 즉, 이 블록에 EXT4 슈퍼 블록이 존재합니다.".format(superblock_offset, hex(superblock_offset)))
            self.superblock_number_list.append(math.floor(superblock_offset / self.file_connector.block_size))
            self.superblock_content_list.append(rblock)
            self.fwrite_superblock(superblock_offset, len(self.superblock_content_list) - 1)
            index += 1

        self.file_connector.load_original_seek()

        writefile = open(r'F:\Android_x86_image\4월15일\carved\super_block_offset_list.txt','w')
        for offset in self.superblock_offset_list:
            writefile.write('{0} 번째 탐지의 offset은 {1}, 이는 {2} 차이\n'.format(self.superblock_offset_list.index(offset),offset,self.superblock_offset_difference_list[self.superblock_offset_list.index(offset)]))
        writefile.close()

#그룹 디스크립터를 찾는 함수입니다. 이 함수가 작동하기 위해서는 먼저 수퍼블록을 카빙해야합니다.
    def find_group_descriptor(self):
        super_block_index = 0
        self.file_connector.save_original_seek()
        while (super_block_index < len(self.superblock_number_list)):
            #파일 시스템의 수퍼블록은 0x400에 있습니다. 해당 수퍼블록의 400을 포함해서 4096바이트 후에 그룹 디스크립터 테이블이 존재합니다.
            """
            if self.superblock_offset_list[super_block_index] <= 0x400:
                self.file_connector.file.seek(self.superblock_offset_list[super_block_index] + 0xC00)
            #저널링 된 수퍼블록은 위의 오프셋 계산과는 관련 없이 바로 다음 블록에 존재합니다.
            else:
                self.file_connector.file.seek(self.superblock_offset_list[super_block_index] + self.file_connector.block_size)

            print(self.file_connector.file.tell())
            content = self.file_connector.temp_file_read(self.file_connector.block_size)
            """
            content = self.file_connector.block_file_read(self.superblock_number_list[super_block_index] + 1)

            t_len = self.group_descriptor_length_list[super_block_index]
            self.group_descriptor_content_list.append([])
            for group_descriptor_index in range(0,self.group_descriptor_many_list[super_block_index]):
                self.group_descriptor_content_list[super_block_index].append([])
                self.group_descriptor_content_list[super_block_index][group_descriptor_index] = content[group_descriptor_index * t_len: (group_descriptor_index + 1) * t_len]

            super_block_index += 1
        self.file_connector.load_original_seek()


#발견한 저널 수퍼블록과 수퍼블록, 그룹 디스크립터 블록을 파싱해서 필요한 데이터를 얻는 함수입니다.
    def parsing_super_block(self, superblock_content_list_index):
        content = self.superblock_content_list[superblock_content_list_index]
        offset = self.superblock_offset_list[superblock_content_list_index] % self.file_connector.block_size

        self.group_descriptor_many_list.append(math.ceil(int.from_bytes(content[offset + 0x4:offset + 0x8],'little') / int.from_bytes(content[offset + 0x20:offset + 0x24],'little')))
        self.group_descriptor_block_many_list.append(int.from_bytes(content[offset + 0x20:offset + 0x24],'little'))
        self.group_descriptor_inode_many_list.append(int.from_bytes(content[offset + 0x28:offset + 0x2C],'little'))
        self.group_descriptor_length_list.append(int.from_bytes(content[offset + 0xFE:offset + 0x100],'little'))
        print('group descriptor 개수? : {0}'.format(self.group_descriptor_many_list[0]))
        print('group descriptor 하나당 블록 개수? : {0}'.format(hex(self.group_descriptor_block_many_list[0])))
        print('group descriptor 하나당 i노드 개수? : {0}'.format(hex(self.group_descriptor_inode_many_list[0])))
        print('group descriptor 길이? : {0}'.format(self.group_descriptor_length_list[0]))

#발견한 그룹 디스크립터 내용을 파싱합니다.
    #def parsing_group_descriptor(self, group_descriptor_list_index):







#수퍼블록과 저널 수퍼블록을 파일로 출력시키는 함수입니다.
    def fwrite_superblock(self, superblock_offset = 0, superblock_content_list_index = 0):
        writefile = open(r'F:\Android_x86_image\4월15일\carved\super_block_offset_{0}'.format(superblock_offset),'wb')
        writefile.write(bytes(self.superblock_content_list[superblock_content_list_index]))
        writefile.close()

    def fwrite_journal_superblock(self):
        writefile = open(r'F:\Android_x86_image\4월15일\carved\journal_super_block', 'wb')
        writefile.write(bytes(self.journal_superblock_content))
        writefile.close()



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




