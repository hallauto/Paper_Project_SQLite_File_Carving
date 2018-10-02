import re
import math
import string
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

        self.ExTSuperBlock_list = []
        self.superblock_many = 0
        self.superblock_number_list = []
        self.superblock_content_list = []
        self.superblock_former_offset = -1
        self.superblock_offset_list = []

#SQLite카빙을 위해 저널 수퍼블록과 수퍼블록, 그룹 디스크립터 블록을 찾아야 합니다. 해당 정보들이 전부 모여야 SQLite 카빙이 가능합니다.

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

#파일 이름이 유효한지 파악하는 함수입니다. 디렉토리 엔트리에서 파일 이름을 확보하는 작업이나 파일 이름이 유효한지 검사하는 작업에 쓰입니다.
    def check_file_name(self, file_name):
        #ExT4에서 유효한 파일 명들을 저장했습니다.
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        valid_chars = bytearray(valid_chars,'ascii')

        if type(file_name) is int or len(file_name) is 1 :
            if type(file_name) is list:
                file_name = file_name[0]
            if file_name not in valid_chars:
                return False
            else:
                return True
        else:
            for file_character in file_name:
                if file_character not in valid_chars:   #유효한 문자 외의 문자가 있는지 검사합니다.
                    return False

            # ExT4에서 파일명의 첫 글자가 특수문자이면 안됩니다.
            if file_name[0] in b"-_.() ":
                return False
            return True

        return True

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

#저널 블록에서 저널 로그들을 확보합니다. 하나의 저널 로그는 하나의 디스크립터 블록으로 시작, 이후에 데이터블록들이 나오고 최후에 커밋 블록이나 리보크 블록이 나오는 것으로 끝납니다.
    def find_journal_log(self):
        journal_log_number = 0
        journal_log_exist = False
        journal_block_flag = 0

        self.file_connector.save_original_seek()

#저널 수퍼블록은 저널 로그와는 관련이 없으며, 저널 로그는 저널 수퍼 블록이 나온 이후에 발견됩니다. 단, 리보크 블록이 존재할 가능성도 있습니다.
        current_block_number = self.journal_superblock_number + 1
        content = self.file_connector.block_file_read(current_block_number)
        journal_block_flag = self.check_journal_block(content)
        while journal_block_flag == 0:
            if journal_block_flag is not self.EXT_J_DB_FLAG:
                current_block_number += 1
                content = self.file_connector.block_file_read(current_block_number)
                journal_block_flag = self.check_journal_block(content)

        while journal_block_flag > 0:
            if journal_block_flag is not self.EXT_J_DB_FLAG:
                current_block_number += 1
                content = self.file_connector.block_file_read(current_block_number)
                journal_block_flag = self.check_journal_block(content)
                continue

            else:
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

    #특정 저널로그의 각각의 데이터 블록에서 sqlite db 파일, 저널 파일에 해당하는 디렉토리 엔트리를 확보하는 함수입니다.
    def find_sqlite_directory_entry(self, journal_log):
        for data_block in journal_log.data_block_content_list:
            db_offset_list = []
            journal_offset_list = []
            #먼저 하나의 데이터블록에 몇개의 db, db-journal 파일이 있는지 검사합니다. .db로 검색하면 .db-journal 파일도 검색되는 점을 유념해서 계산합시다.
            journal_file_many = data_block.count(b'.db-journal')
            db_file_many = data_block.count(b'.db') - journal_file_many

            db_offset = -1
            journal_offset = -1
            for until in range(journal_file_many):
                journal_offset = data_block.find(b'.db-journal', journal_offset + 1)
                if journal_offset < 0:
                    break
                else:
                    journal_offset_list.append(journal_offset)
            for until in range(db_file_many):
                db_offset = data_block.find(b'.db', db_offset + 1)
                if db_offset < 0:
                    break
                elif journal_offset_list.count(db_offset) > 0:
                    continue
                else:
                    db_offset_list.append(db_offset)

#확보한 오프셋은 파일 확장자 명이 시작하는 부분의 오프셋입니다. 이 오프셋 이전부터는 파일 이름과 디렉토리 엔트리 정보가 들어있으며, 이 점을 고려해서 파일 확장자명이 시작하는 부분을 기준으로 조사합니다.
            for journal_name_offset in journal_offset_list:
                journal_name_start = journal_name_offset
                journal_file_name = []
                while self.check_file_name(data_block[journal_name_start - 1]):
                    journal_name_start -= 1
                    journal_file_name.insert(0,data_block[journal_name_start])

                if self.check_file_name(journal_file_name) is False:
                    continue

                journal_file_name_length = int.from_bytes(data_block[journal_name_start - 2: journal_name_start - 1], 'little')
                journal_entry_length = int.from_bytes(data_block[journal_name_start - 4: journal_name_start - 2], 'little')
                journal_i_node_number = int.from_bytes(data_block[journal_name_start - 8: journal_name_start - 4], 'little')
                journal_entry_content = data_block[journal_name_start - 8: journal_name_start - 8 + journal_entry_length - 1]
                journal_file_name = data_block[journal_name_start:journal_name_offset]
                journal_file_name = journal_file_name + b'.db-journal'
                tmp_journal_entry = ExTDirectoryEntry(journal_i_node_number, journal_entry_length, journal_file_name_length, journal_file_name, journal_entry_content)
                journal_log.journal_entry_list.append(tmp_journal_entry)
                journal_log.whole_entry_list.append(tmp_journal_entry)

            for db_name_offset in db_offset_list:
                db_name_start = db_name_offset
                db_file_name = []
                while self.check_file_name(data_block[db_name_start - 1]):
                    db_name_start -= 1
                    db_file_name.insert(0, data_block[db_name_start])

                if self.check_file_name(db_file_name) is False:
                    continue

                db_file_name_length = int.from_bytes(data_block[db_name_start - 2: db_name_start - 1], 'little')
                db_entry_length = int.from_bytes(data_block[db_name_start - 4: db_name_start - 2], 'little')
                db_i_node_number = int.from_bytes(data_block[db_name_start - 8: db_name_start - 4], 'little')
                db_entry_content = data_block[db_name_start - 8: db_name_start - 8 + db_entry_length - 1]
                db_file_name = data_block[db_name_start:db_name_offset]
                db_file_name = db_file_name + b'.db'


                if db_file_name_length != len(db_file_name):
                    continue
                tmp_db_entry = ExTDirectoryEntry(db_i_node_number, db_entry_length, db_file_name_length, db_file_name, db_entry_content)
                journal_log.db_entry_list.append(tmp_db_entry)
                journal_log.whole_entry_list.append(tmp_db_entry)

            #데이터 블록 한개의 분석이 끝났습니다. 다음 데이터 블록으로 이동합니다.

    def print_journal_logs(self):
        return_text = ''
        for journal_log in self.journal_log_list:
            return_text = return_text + journal_log.print_journal_log()

        return return_text

    def prints_whole_entry(self):
        return_text = ''
        for journal_log in self.journal_log_list:
            return_text = return_text + journal_log.prints_whole_entry()

        return return_text

#저널 수퍼블록의 내용을 파싱하는 함수입니다.
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

        self.journal_entry_list = [] #저널 로그의 데이터블록에서 확보한 저널 파일 엔트리 리스트입니다.
        self.db_entry_list = [] #저널 로그의 데이터 블록에서 확보한 db 파일 엔트리 리스트입니다.
        self.whole_entry_list = []

    def print_journal_log(self):
        return_text = ''
        return_text = return_text + "저널 로그 번호: {0},\t저널 디스크립터 블록 번호: {1},\t저널 데이터 블록 갯수: {2}\n".format(self.journal_log_number, self.descriptor_block_number,len(self.data_block_content_list))
        return_text = return_text + "저널 종료 블록 종류: {0},\t저널 종료 블록 번호: {1},\t저널 전체 길이: {2},\t저널 전체 블록 갯수: {3}\n".format(self.end_block_flag, self.end_block_number, len(self.whole_content), self.block_many)

        return return_text

    def prints_journal_entry(self):
        return_text = ''
        for entry in self.journal_entry_list:
            return_text = return_text + "저널 로그 번호: {0}\t".format(self.journal_log_number) + entry.print_entry()

        return return_text

    def prints_db_entry(self):
        return_text = ''
        for entry in self.db_entry_list:
            return_text = return_text + "저널 로그 번호: {0}\t".format(self.journal_log_number) + entry.print_entry()

        return return_text

    def prints_whole_entry(self):
        return_text = ''
        for entry in self.whole_entry_list:
            return_text = return_text + "저널 로그 번호: {0}\t".format(self.journal_log_number) + entry.print_entry()

        return return_text

class ExTDirectoryEntry:
    def __init__(self, i_node_number, entry_length, file_name_length, file_name, entry_content):
        self.file_name = file_name
        self.file_name_without_extension = self.file_name.partition(b'.')[0]
        self.file_name_without_extension = str(self.file_name_without_extension)
        self.file_name_without_extension = self.file_name_without_extension[2:]
        self.file_extension = self.file_name.partition(b'.')[-1]
        self.file_extension = str(self.file_extension)
        self.file_extension = self.file_extension[2:]
        self.file_name_length = file_name_length
        self.i_node_number = i_node_number
        self.entry_length = entry_length
        self.group_descriptor_number = -1
        self.entry_content = entry_content

    def print_entry(self):
        return_text = ''
        return_text = return_text + "디렉토리 엔트리 i-node 번호: {0},\t디렉토리 엔트리 길이: {1},\t디렉토리 엔트리 파일 이름 길이: {2}\n".format(hex(self.i_node_number), hex(self.entry_length), hex(self.file_name_length))
        return_text = return_text + "디렉토리 엔트리 파일 종류: {0},\t디렉토리 엔트리 파일 이름: {1},\t디렉토리 엔트리 전체 길이: {2},\t디렉토리 엔트리 전체 출력: {3}\n".format(self.file_extension, self.file_name, hex(len(self.entry_content)), self.entry_content)

        return return_text


class SuperBlockCarver:

    EXT_SUPER_B_HEADER = b'\x53\xEF\x01\x00'
    EXT_SUPER_B_HEADER_OFFSET = 56

    def __init__(self, file_connector : FileConnector=None):
        self.file_connector = file_connector

        self.ExTSuperBlock_list = []
        self.superblock_many = 0

        self.group_descriptor_start = -1
        self.group_descriptor_list = []
        self.group_descriptor_many = -1
        self.group_descriptor_block_many = -1
        self.group_descriptor_inode_many = -1
        self.group_descriptor_length = -1

    # 수퍼블록을 찾는 함수입니다. 이 함수가 작동하기 위해서는 먼저 저널 수퍼블록을 카빙해야합니다.
    def find_superblock(self, journal_superblock_offset):
        rblock = b'start'
        self.file_connector.save_original_seek()
        index = 0
        while (len(rblock) > 1 and (
                self.file_connector.file.tell() < journal_superblock_offset)):  # super block은 저널 슈퍼 블록보다 전에 있습니다.
            rblock = self.file_connector.block_file_read(index)
            header_offset = rblock.find(self.EXT_SUPER_B_HEADER)
            if (header_offset < 0):
                index += 1
                continue
            tmp_ExtSuperBlock = ExTSuperBlock()
            tmp_ExtSuperBlock.superblock_offset = self.file_connector.file.tell() - self.file_connector.block_size + header_offset - self.EXT_SUPER_B_HEADER_OFFSET
            print(str(hex(
                self.file_connector.file.tell() - self.file_connector.block_size)) + " 헤더 오프셋 {0}({1})이 있습니다. 즉, 이 블록에 EXT4 슈퍼 블록이 존재합니다.".format(
                tmp_ExtSuperBlock.superblock_offset, hex(tmp_ExtSuperBlock.superblock_offset)))
            tmp_ExtSuperBlock.superblock_number = math.floor(
                tmp_ExtSuperBlock.superblock_offset / self.file_connector.block_size)
            tmp_ExtSuperBlock.superblock_content = rblock
            self.superblock_many += 1
            index += 1

            self.ExTSuperBlock_list.append(tmp_ExtSuperBlock)

        self.file_connector.load_original_seek()

    # 그룹 디스크립터를 찾는 함수입니다. 이 함수가 작동하기 위해서는 먼저 수퍼블록을 카빙해야합니다.
    def find_group_descriptor(self):
        super_block_index = 0
        self.file_connector.save_original_seek()
        for ext_super_block in self.ExTSuperBlock_list:
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
            content = self.file_connector.block_file_read(ext_super_block.superblock_number + 1)

            t_len = ext_super_block.group_descriptor_length
            ext_super_block.group_descriptor_content_list = [0 for i in range(0, ext_super_block.group_descriptor_many)]
            for group_descriptor_index in range(0, ext_super_block.group_descriptor_many):
                ext_super_block.group_descriptor_content_list[group_descriptor_index] = content[group_descriptor_index * t_len: (group_descriptor_index + 1) * t_len]

        self.file_connector.load_original_seek()

    # 발견한 저널 수퍼블록과 수퍼블록, 그룹 디스크립터 블록을 파싱해서 필요한 데이터를 얻는 함수입니다.
    def parsing_super_block(self, ext_super_block):
        content = ext_super_block.superblock_content
        offset = ext_super_block.superblock_offset % self.file_connector.block_size

        ext_super_block.group_descriptor_many = math.ceil(int.from_bytes(content[offset + 0x4:offset + 0x8], 'little') / int.from_bytes(content[offset + 0x20:offset + 0x24], 'little'))
        ext_super_block.group_descriptor_block_many = int.from_bytes(content[offset + 0x20:offset + 0x24], 'little')
        ext_super_block.group_descriptor_inode_many = int.from_bytes(content[offset + 0x28:offset + 0x2C], 'little')
        ext_super_block.group_descriptor_length = int.from_bytes(content[offset + 0xFE:offset + 0x100], 'little')
        ext_super_block.inode_structure_size = int.from_bytes(content[offset + 0x58:offset + 0x5A], 'little')
        #통상적으로, 안드로이드에서 내부메모리의 파일시스템의 설정을 바꾸는 경우는 거의 없습니다. 이를 감안해서 첫번째 수퍼블록에서 얻은 설정값을 기본 설정값이라 가정합니다.
        self.group_descriptor_many = ext_super_block.group_descriptor_many
        self.group_descriptor_block_many = ext_super_block.group_descriptor_block_many
        self.group_descriptor_inode_many = ext_super_block.group_descriptor_inode_many
        self.group_descriptor_length = ext_super_block.group_descriptor_length
        print(ext_super_block.print_superblock())

    # 발견한 그룹 디스크립터 내용을 파싱합니다.
    def parsing_group_descriptor(self, ext_superblock):
        for group_descriptor_content in ext_superblock.group_descriptor_content_list:
            content = group_descriptor_content
            bg_block_bitmap_lo = int.from_bytes(content[0:4], 'little')
            bg_inode_bitmap_lo = int.from_bytes(content[4:8], 'little')
            bg_inode_table_lo = int.from_bytes(content[8:0xC], 'little')
            bg_free_blocks_count_lo = int.from_bytes(content[0xC:0xE], 'little')
            bg_free_inodes_count_lo = int.from_bytes(content[0xE:0x10], 'little')
            bg_used_dirs_count_lo = int.from_bytes(content[0x10:0x12], 'little')

            tmp_ExTGroupDescriptor = ExTGroupDescriptor(len(ext_superblock.ExTGroupDescriptor_list), bg_block_bitmap_lo,
                                                        bg_inode_bitmap_lo, bg_inode_table_lo, bg_free_blocks_count_lo,
                                                        bg_free_inodes_count_lo, bg_used_dirs_count_lo)
            ext_superblock.ExTGroupDescriptor_list.append(tmp_ExTGroupDescriptor)

    def print_whole_super_block(self):
        return_text = ''
        for ext_super_block in self.ExTSuperBlock_list:
            return_text = return_text + ext_super_block.print_superblock()

        return return_text

    def print_whole_group_descriptor(self):
        return_text = ''
        for ext_superblock in self.ExTSuperBlock_list:
            for group_descriptor in ext_superblock.ExTGroupDescriptor_list:
                return_text = return_text + group_descriptor.print_group_descriptor()

        return return_text


class ExTSuperBlock:
    def __init__(self):
        self.superblock_number = -1
        self.superblock_content = []
        self.superblock_offset = -1

        self.group_descriptor_start = -1
        self.group_descriptor_content_list = [[]]
        self.group_descriptor_many = -1
        self.group_descriptor_block_many = -1
        self.group_descriptor_inode_many = -1
        self.group_descriptor_length = -1
        self.ExTGroupDescriptor_list = []

        self.inode_structure_size = -1

    def print_superblock(self):
        return_text = ''
        return_text = return_text + 'superblock 블록 번호 : {0}\nsuperblock 오프셋 : {1}\n'.format(self.superblock_number, self.superblock_offset)
        return_text = return_text + 'group descriptor 개수? : {0}\n'.format(self.group_descriptor_many) + 'group descriptor 하나당 블록 개수? : {0}\n'.format(hex(self.group_descriptor_block_many))
        return_text = return_text + 'group descriptor 하나당 i노드 개수? : {0}\n'.format(hex(self.group_descriptor_inode_many)) + 'group descriptor 길이? : {0}\n'.format(self.group_descriptor_length)
        return_text = return_text + 'i node 크기 : {0}\n'.format(self.inode_structure_size)

        return return_text


class ExTGroupDescriptor:
    def __init__(self, group_descriptor_number,bg_block_bitmap_lo, bg_inode_bitmap_lo, bg_inode_table_lo, bg_free_blocks_count_lo, bg_free_inodes_count_lo, bg_used_dirs_count_lo):
        self.group_descriptor_number = group_descriptor_number
        self.bg_block_bitmap_lo = bg_block_bitmap_lo
        self.bg_inode_bitmap_lo = bg_inode_bitmap_lo
        self.bg_inode_table_lo = bg_inode_table_lo
        self.bg_free_blocks_count_lo = bg_free_blocks_count_lo
        self.bg_free_inodes_count_lo = bg_free_inodes_count_lo
        self.bg_used_dirs_count_lo = bg_used_dirs_count_lo

    def print_group_descriptor(self):
        return_text = ''
        return_text = return_text + "그룹 디스크립터 번호: {0},\t그룹 디스크립터 블록 비트맵 위치: {1},\ti-node 비트맵 위치: {2},\ti-node 테이블 위치: {3}\n".format(self.group_descriptor_number, hex(self.bg_block_bitmap_lo), hex(self.bg_inode_bitmap_lo), hex(self.bg_inode_table_lo))
        return_text = return_text + "빈 블록 갯수: {0},\t비할당 i-node 갯수: {1},\t할당된 디렉토리 엔트리 갯수: {2}\n".format(hex(self.bg_free_blocks_count_lo), hex(self.bg_free_inodes_count_lo), self.bg_used_dirs_count_lo)

        return return_text


class ExTInodeTable:
    def __init__(self):
        self.inode_many = -1