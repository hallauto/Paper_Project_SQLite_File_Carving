import os,re

class FileCheck:

    def __init__(self,original_file_dir, comport_file_dir, block_size = 4096):
        self.original_file_dir = original_file_dir
        self.comport_file_dir = comport_file_dir

        self.original_file = -1
        self.comport_file = -1
        self.original_file_list = []
        self.comport_file_list = []

        self.original_file_list = []
        self.comport_file_list = os.listdir(self.comport_file_dir)

        self.original_file_contain_list = []
        self.comport_file_contain_list = []

        self.match_list = []

        for file_name in os.listdir(self.original_file_dir):
            li = []
            if file_name.count('.db') > 0:
                self.original_file_list.append(file_name)

        for file_name in os.listdir(self.comport_file_dir):
            if file_name.count('group') > 0:
                self.comport_file_list.append(file_name)

        self.block_size = block_size


    def read_original_file(self):
        for file_name in self.original_file_list:
            file = open(file_name,'rb')
            self.original_file_contain_list.append(file.read(self.block_size))
            file.close()

    def read_comport_file(self):
        for file_name in self.comport_file_list:
            file = open(file_name, 'rb')
            self.comport_file_contain_list.append(file.read(self.block_size))
            file.close()

    def check_file_list(self):
        original_index = -1
        comport_index = -1
        for file_name in self.original_file_list:
            original_index = self.original_file_list.index(file_name)
            for c_file_name in self.comport_file_list:
                if c_file_name.find(file_name) > -1:
                    comport_index = self.comport_file_list.index(c_file_name)

            if original_index < 0 or comport_index < 0:
                continue

            if self.original_file_contain_list[original_index] == self.comport_file_contain_list[comport_index]:
                self.match_list.append((self.original_file_list[original_index], self.comport_file_list[comport_index]))
            else:
                continue