import sys,os

class FileConnector:
    """ 기존 파일은 다양한 파일시스템에서 사용 가능하지 못할듯 합니다.
        특히 전체 디스크 이미지를 분석하는 경우 같은 특이 사항을 대비한 코드가 필요합니다.
        해당 사항을 적용해야합니다.
    """
    def __init__(self, file_name, block_size=4096):
        self.parser = ''
        self.mem_point = -1
        self.file_type = ""
        self.file_size = -1
        self.block_size = -1
        self.dest_name = -1
        self.src_name = -1
        self.file_open(file_name, block_size)

    def file_open(self, file_name, block_size=4096):
        if file_name.find(".journal") or file_name.find("logdump"):
            self.file_type = 'journal'
            self.src_name = file_name
        elif file_name.find(".dd"):
            self.file_type = 'dd'
            self.file_size = os.path.getsize(file_name)
            self.block_size = block_size
            self.src_name = file_name
        elif file_name.find(".image"):
            self.file_type = 'image'
            self.file_size = os.path.getsize(file_name)
            self.block_size = block_size
            self.src_name = file_name
        elif file_name.find(".db"):
            self.file_type = 'db'
            self.dest_name = file_name
        elif file_name.find(".db-journal"):
            self.file_type = 'db-journal'
            self.dest_name = file_name

        try:
            if self.file_type == 'journal':
                self.file = open(file_name)
            elif self.file_type == 'dd' or self.file_type == 'image':
                self.file = open(file_name, 'rb')
            elif self.file_type == 'db' or self.file_type == 'db-journal':
                self.file = open(file_name, 'w')
        except IOError as error:
            print("파일이 존재하지않습니다.")
        except Exception as error:
            print("An exception happened: " + str(error))

    def reset_file_point(self):
        self.file.seek(0)

    def temp_file_read(self, read_size):
        original_location = self.file.tell()
        read_data = self.file.read(read_size)
        self.file.seek(original_location, 0)
        return read_data

    def save_original_seek(self):
        self.mem_point = self.file.tell()

    def load_original_seek(self):
        if self.mem_point == -1:
            return
        self.file.seek(self.mem_point,0)
        self.mem_point = -1

    def block_file_read(self, block_number):
        try:
            self.file.seek(block_number * self.block_size,0)
            if self.file.readable() is False:
                print("There isn't block number {0}".format(block_number))

            read_data = self.file.read(self.block_size)
            return read_data
        except IOError as error:
            print("There isn't block number {0}")
            return ''


