import math
import string
from FileConnector import FileConnector
from enum import IntEnum
from collections import OrderedDict
import ExTCarving

class CheckBlock:
    def __init__(self, ExTCarver : ExTCarving.EXTCarving):
        self.ext_carver = ExTCarver
        self.ext_sb_carver = ExTCarver.super_b_carver
        self.ext_journal_carver = ExTCarver.journal_carver

        self.db_entry_list = []
        self.db_entry_many = 0
        for journal_log in self.ext_journal_carver:
            self.db_entry_many += len(journal_log.db_entry_list)
            self.db_entry_list.append(journal_log.db_entry_list)

        self.journal_entry_list = []
        self.journal_entry_many = 0
        for journal_log in self.ext_journal_carver:
            self.journal_entry_many += len(journal_log.journal_entry_list)
            self.journal_entry_list.append(journal_log.journal_entry_list)

        self.checked_block_list = []
        self.checked_group_list = []
        self.journal_exist_group_list = []
        self.db_exist_group_list = []
        self.entry_group_tuple_list = []
        self.entry_exist_group_list = []
        self.db_journal_tuple_list = []

        self.group_db_many_list = []
        self.group_journal_many_list = []

#db와 db-journal 파일을 매칭 시키는 함수입니다. 이 함수는 sqlite3에 따라 각 db, db-journal의 이름이 같으면 매칭 시킵니다.
    def make_db_journal_tuple_list(self):
        tmp_matching_tuple = ()
        tmp_matching_dictionary = {}
        checked_file_name_list = []
        for db_entry in self.db_entry_list.reverse():#가장 최근에 변경된 내역을 담은 저널로그가 가장 근접한 정보를 가지리라는 판단하에 저널 로그를 역순으로 탐색합니다.
            #저널로그에는 다수의 엔트리가 존재하며, 하나의 파일에 여러 디렉토리 엔트리가 저널로그에 존재할 수 있습니다. 이러한 중복은 db, db-journal에서는 무시해도 좋습니다.
            if db_entry.file_name in checked_file_name_list:
                continue
            for journal_entry in self.journal_entry_list.reverse():
                if journal_entry.file_name in checked_file_name_list:
                    continue
                if db_entry.entry_file_name_without_extension is journal_entry.file_name_without_extension:
                    checked_file_name_list.append(db_entry.file_name)
                    checked_file_name_list.append(journal_entry.file_name)
                    tmp_matching_tuple = (db_entry, journal_entry)
                    self.db_journal_tuple_list.append(tmp_matching_tuple)

#db와 db-journal파일들의 디렉토리 엔트리가 속한 블록 그룹을 분석해서 매칭하여 만든 튜플들의 리스트를 만드는 함수입니다.
    def make_entry_group_tuple_list(self):
        tmp_entry_group_tuple = ()
        check_duplicate_tuple = ()
        check_duplicate_tuple_list = []
        for db_entry in self.db_entry_list.reverse():
            group = db_entry.i_node_number / self.ext_carver.ExTSuperBlock_list[0].group_descriptor_inode_many

            check_duplicate_tuple = (group, db_entry.file_name)
            if check_duplicate_tuple in check_duplicate_tuple_list:
                continue

            tmp_entry_group_tuple = (group, db_entry)
            self.entry_group_tuple_list.append(tmp_entry_group_tuple)
            check_duplicate_tuple_list.append(check_duplicate_tuple)

        check_duplicate_tuple_list = []
        for journal_entry in self.journal_entry_list.reverse():
            group = journal_entry.i_node_number / self.ext_carver.ExTSuperBlock_list[0].group_descriptor_inode_many

            check_duplicate_tuple = (group, journal_entry.file_name)
            if check_duplicate_tuple in check_duplicate_tuple_list:
                continue

            tmp_entry_group_tuple = (group, journal_entry)
            self.entry_group_tuple_list.append(group)
            check_duplicate_tuple_list.append(check_duplicate_tuple)

#db 파일이 존재하는 블록 그룹 번호를 담은 리스트를 만드는 함수입니다.
    def make_db_exist_group_list(self):
        for db_entry in self.db_entry_list.reverse():
            group = db_entry.i_node_number / self.ext_carver.ExTSuperBlock_list[0].group_descriptor_inode_many
            self.db_exist_group_list.append(group)

        self.db_exist_group_list = OrderedDict.fromkeys(self.db_exist_group_list)

#db-journal 파일이 존재하는 블록 그룹 번호를 담은 리스트를 만드는 함수입니다.
    def make_journal_exist_group_list(self):
        for journal_entry in self.journal_entry_list.reverse():
            group = journal_entry.i_node_number / self.ext_carver.ExTSuperBlock_list[0].group_descriptor_inode_many
            self.journal_exist_group_list.append(group)

        self.journal_exist_group_list = OrderedDict.fromkeys(self.journal_exist_group_list)

#파일 카빙을 할때, 이미 검사된 블록 그룹과 그 블록 그룹에 속한 블록을 기록하는 리스트를 관리하는 함수입니다.
    def mark_group_and_block(self, group = -1, block = -1):
        if group < 0:
            self.checked_block_list.append(block)
        elif block < 0:
            self.checked_group_list.append(group)
            for block in range(group * self.ext_carver.super_b_carver.group_descriptor_block_many, (group + 1) * self.ext_carver.super_b_carver.group_descriptor_block_many):
                self.checked_block_list.append(block)

    def make_entry_exist_group_list(self):
        for db_entry in self.db_entry_list.reverse():
            group = db_entry.i_node_number / self.ext_carver.ExTSuperBlock_list[0].group_descriptor_inode_many
            self.entry_exist_group_list.append(group)

        for journal_entry in self.journal_entry_list.reverse():
            group = journal_entry.i_node_number / self.ext_carver.ExTSuperBlock_list[0].group_descriptor_inode_many
            self.entry_exist_group_list.append(group)

        self.entry_exist_group_list = OrderedDict.fromkeys(self.entry_exist_group_list)



