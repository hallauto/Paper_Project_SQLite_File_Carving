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

    EXT_SUPER_B_HEADER = b'\x53\xEF\x01\x00'
    EXT_SUPER_B_HEADER_OFFSET = 56

    def __init__(self, file_connector : FileConnector=None):
        self.file_connector = file_connector
        self.journal_carver = ExTJournalCarving(file_connector)

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


#수퍼블록을 찾는 함수입니다. 이 함수가 작동하기 위해서는 먼저 저널 수퍼블록을 카빙해야합니다.
    def find_superblock(self):
        rblock = b'start'
        self.file_connector.save_original_seek()
        index = 0
        while(len(rblock) > 1 and (self.file_connector.file.tell() < self.journal_carver.journal_superblock_offset)):  #super block은 저널 슈퍼 블록보다 전에 있습니다.
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
            """
            #파일 시스템의 수퍼블록은 0x400에 있습니다. 해당 수퍼블록의 400을 포함해서 4096바이트 후에 그룹 디스크립터 테이블이 존재합니다.
            
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


class ExTJournalCarving:

    EXT_J_HEADER = b'\xC0\x3B\x39\x98'
    EXT_J_SB_HEADER = b'\xC0\x3B\x39\x98\x00\x00\x00\x04'
    EXT_J_DB_HEADER = b'\xC0\x3B\x39\x98\x00\x00\x00\x01'
    EXT_J_CB_HEADER = b'\xC0\x3B\x39\x98\x00\x00\x00\x02'
    EXT_J_RB_HEADER = b'\xC0\x3B\x39\x98\x00\x00\x00\x05'
    EXT_J_SB_FLAG = 4
    EXT_J_DB_FLAG = 1
    EXT_J_CB_FLAG = 2
    EXT_J_RB_FLAG = 5


    def __init__(self, file_connector : FileConnector=None):
        self.file_connector = file_connector
        self.journal_superblock_offset = -1
        self.journal_block_length = -1
        self.journal_block_many = -1
        self.journal_block_start_number = -1
        self.journal_block_start_offset = -1
        self.journal_superblock_number = -1
        self.journal_superblock_content = []
        self.journal_log_list = []

#저널 블록이 존재하는지 검사하는 함수입니다.
    def check_journal_block(self, block_content = ''):
        if block_content.find(self.EXT_J_SB_HEADER) > -1:
            return self.EXT_J_SB_FLAG
        elif block_content.find(self.EXT_J_DB_HEADER) > -1:
            return self.EXT_J_DB_FLAG
        elif block_content.find(self.EXT_J_CB_HEADER) > -1:
            return self.EXT_J_CB_FLAG
        elif block_content.find(self.EXT_J_RB_HEADER) > -1:
            return self.EXT_J_RB_FLAG

        return 0



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

#파싱한 저널 수퍼블록에서 얻은 내용을 토대로 descriptor 블록을 카빙합니다. - 현재 저널 수퍼블록에서 얻은 내용이 무효화된 저널을 가리키지 않는 문제가 있습니다. 따라서 시그니처를 기반으로 카빙하는 코드가 필요합니다.
    #def find_journal_descriptorblock(self):

#저널 블록에서 저널 로그들을 확보합니다. 하나의 저널 로그는 하나의 디스크립터 블록으로 시작, 이후에 데이터블록들이 나오고 최후에 커밋 블록이나 리보크 블록이 나오는 것으로 끝납니다.
    def find_journal_log(self):
        journal_log_number = 0
        journal_log_exist = False

        self.file_connector.save_original_seek()

#저널 수퍼블록은 저널 로그와는 관련이 없으며, 저널 로그는 저널 수퍼 블록이 나온 이후에 발견됩니다. 단, 리보크 블록이 존재할 가능성도 있습니다.
        current_block_number = self.journal_superblock_number + 1
        content = self.file_connector.block_file_read(current_block_number)

        journal_block_flag = self.check_journal_block(content)

        while(journal_block_flag > 0):
            if (journal_block_flag is self.EXT_J_DB_FLAG):
                temp_journal_log = ExTJournalLog(journal_log_number,self.journal_superblock_offset)
                temp_journal_log.block_number_list.append(current_block_number)
                temp_journal_log.descriptor_block_number = current_block_number
                temp_journal_log.descriptor_content = content
                temp_journal_log.whole_content.append(content)

                current_block_number += 1
                data_block_number = 0
                data_block_content = self.file_connector.block_file_read(current_block_number)
                journal_block_flag = self.check_journal_block(data_block_content)
                #이제 데이터 블록을 확보합니다. 데이터 블록들은 디스크립터 블록과 커밋/리보크 블록 사이에 존재합니다.
                while (journal_block_flag is self.EXT_J_CB_FLAG or journal_block_flag is self.EXT_J_RB_FLAG) is False:
                    temp_journal_log.data_block_number_list.append(current_block_number)
                    temp_journal_log.data_block_content_list.append([])
                    temp_journal_log.data_block_content_list[data_block_number] = data_block_content
                    temp_journal_log.data_block_whole_content_list.append(data_block_content)
                    temp_journal_log.whole_content.append(data_block_content)
                    current_block_number += 1
                    data_block_number += 1
                    data_block_content = self.file_connector.block_file_read(current_block_number)
                    journal_block_flag = self.check_journal_block(data_block_content)
                    if data_block_number > 100:
                        break

                if data_block_number > 100:
                    break
                #커밋/리보크 블록이 발견되었습니다. 해당 저널 로그가 완성되었습니다. 이를 백업합니다.
                temp_journal_log.block_many = data_block_number + 2 #저널 로그의 전체 블록 갯수는 데이터블록 갯수 + 디스크립터 블록(1개) + 커밋/리보크 블록(1개) 입니다.
                temp_journal_log.end_block_number = current_block_number
                temp_journal_log.end_block_flag = journal_block_flag
                temp_journal_log.end_block_content = self.file_connector.block_file_read(temp_journal_log.end_block_number)
                temp_journal_log.whole_content.append(temp_journal_log.end_block_content)
                self.journal_log_list.append(temp_journal_log)

            #성공적으로 하나의 저널로그를 파싱했습니다. 이제 다음 저널 로그가 존재하는지 검사합니다. 다음 저널로그가 존재한다면 바로 디스크립터 블록이 존재할 것이고, 아니면 저널 영역이 끝났다는 의미입니다.
            journal_log_number += 1
            current_block_number += 1
            content = self.file_connector.block_file_read(current_block_number)
            journal_block_flag = self.check_journal_block(content)

        self.file_connector.load_original_seek()

        return

    def print_journal_logs(self):
        return_text = ''
        for journal_log in self.journal_log_list:
            return_text = return_text + "저널 로그 번호: {0},\t저널 디스크립터 블록 번호: {1},\t저널 데이터 블록 갯수: {2}\n".format(journal_log.journal_log_number, journal_log.descriptor_block_number, len(journal_log.data_block_content_list))
            return_text = return_text + "저널 종료 블록 종류: {0},\t저널 종료 블록 번호: {1},\t저널 전체 길이: {2},\t저널 전체 블록 갯수: {3}\n".format(journal_log.end_block_flag, journal_log.end_block_number, len(journal_log.whole_content), journal_log.block_many)

        return return_text

    def find_sqlite_directory_entry(self, journal_log):
        for data_block in journal_log.data_block_content_list:
            db_offset_list = []
            journal_offset_list = []
            #먼저 하나의 데이터블록에 몇개의 db, db-journal 파일이 있는지 검사합니다. .db로 검색하면 .db-journal 파일도 검색되는 점을 유념해서 계산합시다.
            journal_file_many = data_block.count('.db-journal')
            db_file_many = data_block.count('.db') - journal_file_many

            db_offset = -1
            journal_offset = -1
            for until in list(journal_file_many):
                journal_offset = data_block.find('.db-journal', journal_offset)
                if journal_offset < 0:
                    break
                else:
                    journal_offset_list.append(journal_offset)
            for until in list(db_file_many):
                db_offset = data_block.find('.db', db_offset)
                if db_offset < 0:
                    break
                elif journal_offset_list.count(db_offset) > 0:
                    continue
                else:
                    db_offset_list.append(db_offset)


    def parse_journal_superblock(self):
        self.journal_block_length = int.from_bytes(self.journal_superblock_content[0x0C:0x10],'big')
        self.journal_block_many = int.from_bytes(self.journal_superblock_content[0x10:0x14],'big')
        self.journal_block_start_number = int.from_bytes(self.journal_superblock_content[0x18:0x1C],'big')
        self.journal_block_start_offset = self.file_connector.block_size * self.journal_block_start_number
        
        print('journal 블록 크기: {0}'.format(self.journal_block_length))
        print('journal 전체 갯수: {0}({1})'.format(self.journal_block_many,hex(self.journal_block_many)))


    def fwrite_journal_superblock(self):
        writefile = open(r'F:\Android_x86_image\4월15일\carved\journal_super_block', 'wb')
        writefile.write(bytes(self.journal_superblock_content))
        writefile.close()


#ExT 저널 로그를 담는 클래스입니다. 저널 로그를 더 간편한게 접근할 수 있는 함수들도 구현 예정입니다.
class ExTJournalLog:
    def __init__(self, journal_log_number, journal_superblock_offset, block_size = 4096):
        self.journal_log_number = journal_log_number
        self.journal_superblock_offset = journal_superblock_offset
        self.journal_superblock_number = math.floor(journal_superblock_offset / block_size)

        self.whole_content = []
        self.journal_log_length = -1
        self.block_many = -1
        self.block_number_list = []
        self.descriptor_block_number = -1
        self.end_block_number = -1
        self.end_block_flag = -1    #저널 로그의 마지막 블록의 종류는 이를 가리키는 코드 값으로 표현합니다.
        self.data_block_number_list = []
        self.descriptor_content = []
        self.end_block_content = []
        self.data_block_content_list = [] #저널 로그의 데이터 블록 각각의 내용을 담고있습니다.
        self.data_block_whole_content_list = [] #저널 로그의 데이터 블록 내용 전체를 하나의 리스트로 담고있습니다.

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




