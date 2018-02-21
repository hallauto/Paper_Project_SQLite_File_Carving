import sys,os,FileConnector

class FileCarving:
    SQLite_HEADER_STRING = 'SQLite format 3\x00'
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
        self.file_type = [] #카빙해야할 SQLite 파일 타입을 알려주는 값입니다.
        self.journaled_block_numbers = [] #ExT4 Journal을 파싱해서 확인한 저널링 된 블록들입니다. 이들을 먼저 분석합니다.
        self.max_block_number = 0 #현재 분석중인 이미지 파일의 최대 블록 번호입니다.
        self.current_block_number = 0 #현재 분석중인 블록 번호입니다.
        self.investigate_block_numbers = [] #분석해야할 블록 번호입니다. journaled_block_numbers 들이 먼저 분석되므로, 해당 번호의 블록들은 이 목록에서 이후에 삭제됩니다.


    def set_open_file(self, image_file_dir):
        """
        파일 경로를 받고 해당 파일을 읽습니다. 이 함수는 파일 카빙만을 할 때 사용하는 함수입니다.
        :param image_file_dir: 파일 카빙을 진행할 이미지 파일입니다.
        :return:
        """
        try:
            self.image_file = open(image_file_dir)
        except FileNotFoundError:
            print('해당 파일이 없습니다.')

    def set_opened_file(self, image_file):
        """
        열린 file 변수를 전달 받습니다. 해당 변수는 FileConnector에 존재합니다.
        :param image_file: FileConnector에 존재하는 파일 변수를 전달받으면 됩니다.
        :return:
        """
        self.image_file = image_file
        if not self.image_file.readable():
            print('FileConnecotr에서 전달받은 file 변수가 정상적이지 않습니다.')
            self.image_file = None
            return

    def carving_whole_file(self):
        """
        현재 지정된 이미지 파일을 카빙합니다. 해당 카빙 결과는 지정된 디렉토리에 저장됩니다.
        :return:
        """


        return

    def carving_block(self, block_location = -1):
        """
        블록을 읽고 SQLite Header가 있는지 검사한 후에 검사 결과에 따라 카빙을 처리합니다. 모든 블록을 검사할때 까지 카빙은 멈추지 않습니다.
        :param block_text: 파악해야할 블록 텍스트입니다. default 값을 입력하면 current_block_number로 바뀝니다.
        :return:
        """
        if block_location == -1:
            block_location = self.current_block_number

        self.current_block_number = block_location

        block_data = self.fileConnector.block_file_read(block_location)
        if self.check_file_structure(block_data):
            self.investigate_block_numbers.remove(block_location)
            if self.investigate_block_numbers.__len__() < 1:
                while self.file_many > 0:
                    self.fileConnector.file.seek(self.head_offsets[self.file_many -1], 0)
                    sql_db_file_data = self.fileConnector.file.read(self.page_sizes[self.file_many -1]) #먼저 헤더 부분과 첫번째 페이지를 읽습니다. 이후에 추가 페이지가 존재하는지 검사해야합니다.
                    #추가 페이지들은 트리구조로 이어집니다. 따라서, 이들 페이지만의 페이지 헤더가 존재하면 파일이 이어진다고 볼 수 있습니다.
                    leap_page_data = "start" #첫 루프가 무조건 실행되기위한 임시 값입니다.
                    while (len(leap_page_data) > 1):
                        leap_page_data = self.fileConnector.file.read(self.page_sizes[self.file_many -1])
                        if ((leap_page_data[0] != '\x00') and (leap_page_data[0] != '\x0D') and (leap_page_data[0] != '\x0A') and (
                                leap_page_data[0] != '\x05') and (
                                leap_page_data[0] != '\x02')):
                            break
                        if ((ord(leap_page_data[1]) * 256 + ord(leap_page_data[2]) > self.page_sizes[self.file_many-1]) or (
                                ord(leap_page_data[5]) * 256 + ord(leap_page_data[6]) > self.page_sizes[self.file_many-1])):
                            break
                        sql_db_file_data += leap_page_data






    def check_file_structure(self, block_data):
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
        self.file_many+=1

        return True






