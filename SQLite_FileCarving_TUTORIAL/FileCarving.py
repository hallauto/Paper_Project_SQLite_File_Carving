import sys,os,FileConnector,struct

class FileCarving:
    SQLite_HEADER_STRING = 'SQLite format 3\x00'
    SQLite_JOURNAL_HEADER_STRING = b'\xd9\xd5\x05\xf9 \xa1c\xd7'
    
    SQLite_DB = 'db'
    SQLite_JOURNAL = 'journal'
    
    def __init__(self, destdir, fileConnector = None):
        """
        생성자입니다.
        :param destdir: 카빙된 파일이 저장될 디렉토리입니다.
        """
        self.destdir = destdir
        self.fileConnector = fileConnector
        self.file_many = 0
        self.head_offsets = [] #카빙해야할 파일들의 head가 시작되는 offset입니다.
        self.page_sizes = [] #카빙해야할 SQLite 파일들의 page size 입니다.
        self.sector_sizes = [] #카빙해야할 SQLite 저널 파일들이 알려주는 sector size 입니다. 저널파일은 이 크기만큼 헤더가 존재하고 그 이후에 페이지가 시작됩니다. db 파일은 해당 사이즈를 이용하지 않으며, 따라서 -1로 값을 넣습니다.
        self.file_type = [] #카빙해야할 SQLite 파일 타입을 알려주는 값입니다.
        self.journaled_block_numbers = [] #ExT4 Journal을 파싱해서 확인한 저널링 된 블록들입니다. 이들을 먼저 분석합니다.
        self.max_block_number = self.fileConnector.file_size/self.fileConnector.block_size #현재 분석중인 이미지 파일의 최대 블록 번호입니다.
        self.current_block_number = 0 #현재 분석중인 블록 번호입니다.
        self.investigate_block_numbers = list[range(0,self.max_block_number)] #분석해야할 블록 번호입니다. journaled_block_numbers 들이 먼저 분석되므로, 해당 번호의 블록들은 이 목록에서 이후에 삭제됩니다.


    def carving_block(self, block_location = -1):
        """
        블록을 읽고 SQLite Header가 있는지 검사한 후에 검사 결과에 따라 카빙을 처리합니다. 모든 블록을 검사할때 까지 카빙은 멈추지 않습니다.
        :param block_text: 파악해야할 블록 텍스트입니다. default 값을 입력하면 current_block_number로 바뀝니다.
        :return:
        """
        if block_location == -1:
            block_location = self.current_block_number

        self.current_block_number = block_location

        block_data = self.fileConnector.block_file_read(block_location)  #검사할 블록을 읽습니다.
        self.investigate_block_numbers.remove(block_location)
        if self.check_db_file_structure(block_data) or self.check_journal_file_structure():
            return True
        return False
                    
    def carving_whole_file(self):
        """
        현재 지정된 이미지 파일 전체를 카빙합니다. 해당 카빙 결과는 지정된 디렉토리에 저장됩니다.
        :return:
        """
        for self.current_block_number in self.investigate_block_numbers:
            self.carving_block(self.current_block_number)





        return

    def make_file(self, index):
        """
        지시된 인덱스에 저장된 오프셋, 사이즈에 따라 파일을 카빙합니다. 카빙된 부분도 분석할 블록 목록에서 제거해야합니다.
        :param index: page_sizes,head_offsets 등에 접근할 때 쓸 색인입니다.
        :return:
        """

        if index > len(self.page_sizes) or index > len(self.head_offsets):
            return False
        if len(self.page_sizes) != len(self.head_offsets):
            return False

        page_per_block = abs(self.page_sizes[index]/self.fileConnector.block_size)

        self.fileConnector.file.seek(self.index, 0)
        #먼저 저널 파일을 카빙하는지, DB 파일을 카빙하는지 검사합니다.
        if self.file_type == self.SQLite_DB:
            sql_file_data = self.fileConnector.file.read(self.page_sizes[index])  # 먼저 헤더 부분과 첫번째 페이지를 읽습니다. 이후에 추가 페이지가 존재하는지 검사해야합니다.
            # 추가 페이지들은 트리구조로 이어집니다. 따라서, 이들 페이지만의 페이지 헤더가 존재하면 파일이 이어진다고 볼 수 있습니다.
            leap_page_data = "start"  # 첫 루프가 무조건 실행되기위한 임시 값입니다.
            while len(leap_page_data) > 1:
                leap_page_data = self.fileConnector.file.read(self.page_sizes[index])
                if ((leap_page_data[0] != '\x00') and (leap_page_data[0] != '\x0D') and (
                        leap_page_data[0] != '\x0A') and (
                        leap_page_data[0] != '\x05') and (
                        leap_page_data[0] != '\x02')):
                    break
                if ((ord(leap_page_data[1]) * 256 + ord(leap_page_data[2]) > self.page_sizes[index]) or (
                        ord(leap_page_data[5]) * 256 + ord(leap_page_data[6]) > self.page_sizes[index])):
                    break
                sql_file_data += leap_page_data

        #저널 파일 카빙입니다.
        if self.file_type == self.SQLite_JOURNAL:
            if self.sector_sizes[index] == -1:
                return False
            sql_file_data == self.fileConnector.file.read(self.sector_sizes[index] + self.page_sizes[index])
            journal_page_data = 'start'
            while (len(journal_page_data) > 3):
                journal_page_data = self.fileConnector.file.read(self.page_sizes[index])
                # 페이지 번호가 0 이하일 수는 없습니다.
                try:
                    if struct.unpack('L', bytearray(journal_page_data[0:4]))[0] <= 0:
                        break
                except ValueError:
                    break
                sql_file_data += journal_page_data



    def check_db_file_structure(self, block_data):
        head_offset = block_data.find(FileCarving.SQLite_HEADER_STRING.encode('utf-8'))
        if head_offset == -1:
            return False

        print(str(hex(self.fileConnector.file.tell())) + "헤더 오프셋이 있습니다. 즉, 이 블록에 SQLite 파일이 존재합니다.")
        self.fileConnector.file.seek(-1 * (self.fileConnector.block_size - head_offset), 1) #헤더 오프셋이 유효한지 파악하기위해 헤더 오프셋으로 이동합니다.
        check_data = self.fileConnector.temp_file_read(self.fileConnector.block_size) #헤더 오프셋에서 블록 사이즈 만큼 읽습니다. 유효한 데이터가 존재하는지 파악하기 위함입니다.

        print("check_data[21] = " + str(check_data[21]))
        if (check_data[21] != 64 and check_data[22] != 32 and check_data[23] != 32): #추가로 시그니처 정보를 파악합니다.
            print(str(hex(self.fileConnector.file.tell() - 512)) + "...그러나 파일은 없네요.")
            return False

        page_size = (check_data[16] * 256 + check_data[17])
        print("page size = " + str(page_size))
        if (page_size <= -1):
            return False

        #드디어 파일을 찾았습니다. 해당 파일의 Offset을 정리해서 변수에 저장합니다!
        self.head_offsets.append(head_offset + self.fileConnector.file.tell() - self.fileConnector.block_size) #head_offset은 블록 읽기에서 발견한 head 위치 + 현재까지 읽은 파일 위치 - 현재 작업중인 블록의 크기 입니다.
        self.page_sizes.append(page_size)
        self.file_type.append(self.SQLite_DB)
        self.sector_sizes.append(-1)
        self.file_many+=1

        return True

    def check_journal_file_structure(self, block_data):
        head_offset = block_data.find(FileCarving.SQLite_JOURNAL_HEADER_STRING)
        if head_offset == -1:
            return False
        
        print(str(hex(self.fileConnector.file.tell())) + "헤더 오프셋이 있습니다. 즉, 이 블록에 SQLite 저널 파일이 존재합니다.")
        self.fileConnector.file.seek(-1 * (self.fileConnector.block_size - head_offset), 1) #헤더 오프셋이 유효한지 파악하기위해 헤더 오프셋으로 이동합니다.
        check_data = self.fileConnector.temp_file_read(self.fileConnector.block_size) #헤더 오프셋에서 블록 사이즈 만큼 읽습니다. 유효한 데이터가 존재하는지 파악하기 위함입니다.
        try:
            page_count = struct.unpack('L', bytearray(check_data[8:12]))[0]
            print("rblcok[8] : The number of pages in the next segment of the journal = " + str(page_count))
            checksum = struct.unpack('L', bytearray(check_data[12:16]))[0]
            print("rblcok[12] : A random nonce for the checksum = " + str(checksum))
            initial_db_size = struct.unpack('L', bytearray(check_data[16:20]))[0]
            print("rblcok[16] : Initial size of the database in pages = " + str(initial_db_size))
            sector_size = struct.unpack('L', bytearray(check_data[20:24]))[0]
            print("rblcok[20] : Size of a disk sector assumed by the process that wrote this journal = " + str(
                sector_size))
            page_size = struct.unpack('L', bytearray(check_data[24:28]))[0]
            print("rblcok[24] : Size of pages in this journal = " + str(page_size))

        except ValueError:
            return False

        if initial_db_size <= 0:
            print("error : initial_page_size = [0]".format(initial_db_size), )
            return False
        if sector_size <= 0:
            print("error : sector_size = [0]".format(sector_size), )
            return False
        if page_size <= 0:
            print("error : page_size = [0]".format(page_size), )
            return False

        # 드디어 파일을 찾았습니다. 해당 파일의 Offset을 정리해서 변수에 저장합니다!
        self.head_offsets.append(head_offset + self.fileConnector.file.tell() - self.fileConnector.block_size)  # head_offset은 블록 읽기에서 발견한 head 위치 + 현재까지 읽은 파일 위치 - 현재 작업중인 블록의 크기 입니다.
        self.page_sizes.append(page_size)
        self.file_type.append(self.SQLite_DB)
        self.sector_sizes.append(sector_size)
        self.file_many += 1





