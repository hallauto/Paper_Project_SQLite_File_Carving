import sys,os,struct

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

    def file_open(self, file_name, block_size=4096):
        if file_name.find(".journal") > -1 or file_name.find("logdump") > -1:
            self.file_type = 'journal'
            self.src_name = file_name
        elif file_name.find(".dd") > -1:
            self.file_type = 'dd'
            self.file_size = os.path.getsize(file_name)
            self.block_size = block_size
            self.src_name = file_name
        elif file_name.find(".image") > -1:
            self.file_type = 'image'
            self.file_size = os.path.getsize(file_name)
            self.block_size = block_size
            self.src_name = file_name
        elif file_name.find(".db") > -1:
            self.file_type = 'db'
            self.dest_name = file_name
        elif file_name.find(".db-journal") > -1:
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

#file의 포인터를 0으로 리셋합니다.
    def reset_file_point(self):
        self.file.seek(0)

#file의 일정 크기를 읽습니다. 이 읽기 작업은 file의 포인터에 영향을 주지 않습니다.
    def temp_file_read(self, read_size):
        original_location = self.file.tell()
        read_data = self.file.read(read_size)
        self.file.seek(original_location, 0)
        return read_data

#file의 특정 블록을 읽습니다. 이 읽기 작업은 file의 포인터에 영향을 주지 않습니다.
    def temp_block_read(self, block_number):
        original_location = self.file.tell()
        try:
            self.file.seek(block_number * self.block_size,0)
            if self.file.readable() is False:
                print("There isn't block number {0}".format(block_number))

            read_data = self.file.read(self.block_size)
        except IOError as error:
            print("There isn't block number {0}")
            return ''
        finally:
            self.file.seek(original_location, 0)
        return read_data

#기존의 file 포인터를 저장합니다. 이를 변경해서 다음 함수가 특정 포인터로 빠르게 접근할 수 있게 만들거나, 특정 작업후 기존 포인터로 귀환하는 것이 가능합니다.
    def save_original_seek(self):
        self.mem_point = self.file.tell()

#저장해두었던 file 포인터로 이동합니다.
    def load_original_seek(self):
        if self.mem_point == -1:
            return
        self.file.seek(self.mem_point,0)
        self.mem_point = -1

#file의 특정 블록을 읽습니다.
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

#아래의 함수가 제대로 작동하지 않습니다. 너무 다양한 길이의 타입이 존재해서 이를 읽고 타입에 따라 엔디안을 처리하는 것은 효율적이지 않습니다.
#ext 메타데이터는 small_endian을 사용합니다. 이를 변환하는 것을 잊지 맙시다. 아래의 함수는 해당 변환까지 처리하고 블록을 읽어주는 함수입니다.
    def block_file_read_small_to_big(self, block_number):
        try:
            self.file.seek(block_number * self.block_size,0)
            if self.file.readable() is False:
                print("There isn't block number {0}".format(block_number))

            read_data = self.file.read(self.block_size)

            converted_data = bytearray(len(read_data))
            converted_data[0::2] = read_data[1::2]
            converted_data[1::2] = read_data[0::2]

            return converted_data
        except IOError as error:
            print("There isn't block number {0}")
            return ''

#레포트 전용 저장 파일에 레포트를 저장하고 관리하는 클래스입니다.
class ReportFile:
    def __init__(self):
        self.report_flag = False
        self.report_file = 0

    def report_on(self, file_directory):
        self.report_flag = True
        self.report_file = open(file_directory, 'w')

    def report_write(self, text):
        if self.report_flag is True:
            self.report_file.write(text)

    def report_end(self):
        if self.report_flag is True:
            self.report_file.close()