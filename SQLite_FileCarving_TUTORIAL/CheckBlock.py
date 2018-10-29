import math
import string
from FileConnector import FileConnector
from enum import IntEnum
from collections import OrderedDict
import ExTCarving
import math

class CheckBlock:
    def __init__(self, ExTCarver : ExTCarving.EXTCarving):
        self.ext_carver = ExTCarver
        self.super_b_carver = ExTCarver.super_b_carver
        self.ext_journal_carver = ExTCarver.journal_carver

        self.db_entry_list = []
        self.db_entry_many = 0
        for journal_log in self.ext_journal_carver.journal_log_list:
            if len(journal_log.db_entry_list) > 0:
                self.db_entry_many += len(journal_log.db_entry_list)
                self.db_entry_list += journal_log.db_entry_list

        self.journal_entry_list = []
        self.journal_entry_many = 0
        for journal_log in self.ext_journal_carver.journal_log_list:
            if len(journal_log.journal_entry_list) > 0:
                self.journal_entry_many += len(journal_log.journal_entry_list)
                self.journal_entry_list += journal_log.journal_entry_list

        self.journal_exist_group_list = []
        self.db_exist_group_list = []
        self.entry_exist_group_list = []
        self.db_journal_tuple_list = []

        self.group_entry_list = []
        for group_number in range(0, self.super_b_carver.group_descriptor_many):
            tmp_group_entry = GroupEntry(group_number)
            self.group_entry_list.append(tmp_group_entry)

        self.group_db_many_list = [0 for num in range(0, self.super_b_carver.group_descriptor_many)]
        self.group_journal_many_list = [0 for num in range(0, self.super_b_carver.group_descriptor_many)]
        self.group_entry_many_list = [0 for num in range(0, self.super_b_carver.group_descriptor_many)]

#db와 db-journal 파일을 매칭 시키는 함수입니다. 이 함수는 sqlite3에 따라 각 db, db-journal의 이름이 같으면 매칭 시킵니다.
    def make_db_journal_tuple_list(self):
        tmp_db_list = self.db_entry_list
        tmp_journal_list = self.journal_entry_list
        tmp_db_list.reverse()
        tmp_journal_list.reverse()
        tmp_matching_tuple = ()
        tmp_matching_dictionary = {}
        checked_file_name_list = []
        for db_entry in tmp_db_list:#가장 최근에 변경된 내역을 담은 저널로그가 가장 근접한 정보를 가지리라는 판단하에 저널 로그를 역순으로 탐색합니다.
            #저널로그에는 다수의 엔트리가 존재하며, 하나의 파일에 여러 디렉토리 엔트리가 저널로그에 존재할 수 있습니다. 이러한 중복은 db, db-journal에서는 무시해도 좋습니다.
            if db_entry.file_name in checked_file_name_list:
                continue
            for journal_entry in tmp_journal_list:
                if journal_entry.file_name in checked_file_name_list:
                    continue
                if db_entry.file_name_without_extension is journal_entry.file_name_without_extension:
                    checked_file_name_list.append(db_entry.file_name)
                    checked_file_name_list.append(journal_entry.file_name)
                    tmp_matching_tuple = (db_entry, journal_entry)
                    self.db_journal_tuple_list.append(tmp_matching_tuple)

#db 파일이 존재하는 블록 그룹 번호를 담은 리스트를 만드는 함수입니다.
    def make_db_exist_group_list(self):
        tmp_list = self.db_entry_list
        tmp_list.reverse()
        for db_entry in tmp_list:
            group = math.floor(db_entry.i_node_number / self.ext_carver.super_b_carver.group_descriptor_inode_many)
            self.db_exist_group_list.append(group)

        self.db_exist_group_list = list(OrderedDict.fromkeys(self.db_exist_group_list))

#db-journal 파일이 존재하는 블록 그룹 번호를 담은 리스트를 만드는 함수입니다.
    def make_journal_exist_group_list(self):
        tmp_list = self.journal_entry_list
        tmp_list.reverse()
        for journal_entry in tmp_list:
            group = math.floor(journal_entry.i_node_number / self.ext_carver.super_b_carver.group_descriptor_inode_many)
            self.journal_exist_group_list.append(group)

        self.journal_exist_group_list = list(OrderedDict.fromkeys(self.journal_exist_group_list))

    def make_entry_exist_group_list(self):
        tmp_db_list = self.db_entry_list
        tmp_journal_list = self.journal_entry_list
        tmp_db_list.reverse()
        tmp_journal_list.reverse()
        for db_entry in tmp_db_list:
            group = math.floor(db_entry.i_node_number / self.ext_carver.super_b_carver.group_descriptor_inode_many)
            self.entry_exist_group_list.append(group)

        for journal_entry in tmp_journal_list:
            group = math.floor(journal_entry.i_node_number / self.ext_carver.super_b_carver.group_descriptor_inode_many)
            self.entry_exist_group_list.append(group)

        self.entry_exist_group_list = list(OrderedDict.fromkeys(self.entry_exist_group_list))

    def make_group_many_list(self):
        for db_entry in self.db_entry_list:
            self.group_db_many_list[math.floor(db_entry.i_node_number / self.ext_carver.super_b_carver.group_descriptor_inode_many)] += 1
        for journal_entry in self.journal_entry_list:
            if math.floor(journal_entry.i_node_number / self.ext_carver.super_b_carver.group_descriptor_inode_many) > len(self.group_journal_many_list):
                self.journal_entry_list.remove(journal_entry)
                continue
            self.group_journal_many_list[math.floor(journal_entry.i_node_number / self.ext_carver.super_b_carver.group_descriptor_inode_many)] += 1

    def make_group_entry_list(self):
        for db_entry in self.db_entry_list:
            self.group_entry_list[math.floor(db_entry.i_node_number / self.ext_carver.super_b_carver.group_descriptor_inode_many)].db_entry_list.append(db_entry)
            self.group_entry_list[math.floor(db_entry.i_node_number / self.ext_carver.super_b_carver.group_descriptor_inode_many)].whole_entry_list.append(db_entry)
            self.group_entry_list[math.floor(db_entry.i_node_number / self.ext_carver.super_b_carver.group_descriptor_inode_many)].db_entry_many +=1
            self.group_entry_list[math.floor(db_entry.i_node_number / self.ext_carver.super_b_carver.group_descriptor_inode_many)].whole_entry_many += 1

        for journal_entry in self.journal_entry_list:
            self.group_entry_list[math.floor(journal_entry.i_node_number / self.ext_carver.super_b_carver.group_descriptor_inode_many)].journal_entry_list.append(journal_entry)
            self.group_entry_list[math.floor(journal_entry.i_node_number / self.ext_carver.super_b_carver.group_descriptor_inode_many)].whole_entry_list.append(journal_entry)
            self.group_entry_list[math.floor(journal_entry.i_node_number / self.ext_carver.super_b_carver.group_descriptor_inode_many)].journal_entry_many += 1
            self.group_entry_list[math.floor(journal_entry.i_node_number / self.ext_carver.super_b_carver.group_descriptor_inode_many)].whole_entry_many += 1

        for group in self.group_entry_list:
            group.make_least_entry_list()


class GroupEntry:
    def __init__(self, group_number, db_entry_list = [], journal_entry_list = []):
        self.group_number = group_number
        self.db_entry_list = db_entry_list
        self.journal_entry_list = journal_entry_list
        self.whole_entry_list = db_entry_list + journal_entry_list

        self.db_entry_many = len(db_entry_list)
        self.journal_entry_many = len(journal_entry_list)
        self.whole_entry_many = self.db_entry_many + self.journal_entry_many

        self.least_db_entry_list = []
        self.least_journal_entry_list = []

    def make_least_entry_list(self):
        checked_file_name_list = []
        tmp_db_list = self.db_entry_list
        tmp_journal_list = self.journal_entry_list
        tmp_db_list.reverse()
        tmp_journal_list.reverse()
        for db_entry in tmp_db_list:  # 가장 최근에 변경된 내역을 담은 저널로그가 가장 근접한 정보를 가지리라는 판단하에 저널 로그를 역순으로 탐색합니다.
            # 저널로그에는 다수의 엔트리가 존재하며, 하나의 파일에 여러 디렉토리 엔트리가 저널로그에 존재할 수 있습니다. 이러한 중복은 db, db-journal에서는 무시해도 좋습니다.
            if db_entry.file_name in checked_file_name_list:
                continue
            self.least_db_entry_list.append(db_entry)
            checked_file_name_list.append(db_entry.file_name)
        for journal_entry in tmp_journal_list:
            if journal_entry.file_name in checked_file_name_list:
                continue
            self.least_journal_entry_list.append(journal_entry)
            checked_file_name_list.append(journal_entry.file_name)

        self.sorting_least_db_entry_inode()
        self.sorting_least_journal_entry_inode()

    def sorting_whole_entry_inode(self):
        inode_list = []
        sorted_list = [0 for entry in self.whole_entry_list]
        for entry in self.whole_entry_list:
            inode_list.append(entry.i_node_number)

        inode_list.sort()

        for entry in self.whole_entry_list:
            sorted_list[inode_list.index(entry.i_node_number)] = entry

        self.whole_entry_list = sorted_list

    def sorting_db_entry_inode(self):
        inode_list = []
        sorted_list = [0 for entry in self.db_entry_list]
        for entry in self.db_entry_list:
            inode_list.append(entry.i_node_number)

        inode_list.sort()

        for entry in self.db_entry_list:
            sorted_list[inode_list.index(entry.i_node_number)] = entry

        self.db_entry_list = sorted_list

    def sorting_journal_entry_inode(self):
        inode_list = []
        sorted_list = [0 for entry in self.journal_entry_list]
        for entry in self.journal_entry_list:
            inode_list.append(entry.i_node_number)

        inode_list.sort()

        for entry in self.journal_entry_list:
            sorted_list[inode_list.index(entry.i_node_number)] = entry

        self.journal_entry_list = sorted_list

    def sorting_least_db_entry_inode(self):
        inode_list = []
        sorted_list = [0 for entry in self.least_db_entry_list]
        for entry in self.least_db_entry_list:
            inode_list.append(entry.i_node_number)

        inode_list.sort()

        for entry in self.least_db_entry_list:
            sorted_list[inode_list.index(entry.i_node_number)] = entry

        self.least_db_entry_list = sorted_list

    def sorting_least_journal_entry_inode(self):
        inode_list = []
        sorted_list = [0 for entry in self.least_journal_entry_list]
        for entry in self.least_journal_entry_list:
            inode_list.append(entry.i_node_number)

        inode_list.sort()

        for entry in self.least_journal_entry_list:
            sorted_list[inode_list.index(entry.i_node_number)] = entry

        self.least_journal_entry_list = sorted_list

