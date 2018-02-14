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
        self.file_number = 0
        self.block_number = 0
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

    def read_block(self, block_location = -1):
        """
        블록을 읽고 SQLite Header가 있는지 검사합니다.
        :param block_text: 파악해야할 블록 텍스트입니다. default 값을 입력하면 current_block_number로 바뀝니다.
        :return:
        """
        if block_location is -1:
            block_location = self.current_block_number

        self.fileConnector.read

