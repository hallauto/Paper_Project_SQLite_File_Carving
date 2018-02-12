import sys,os

class FileCarving:
    SQLite_HEADER_STRING = 'SQLite format 3\x00'
    def __init__(self, destdir):
        """
        생성자입니다.
        :param destdir: 카빙된 파일이 저장될 디렉토리입니다.
        """
        self.destdir = destdir
        self.image_file = ''
        self.file_number = 0

    def __init__(self, dsetdir, image_file):
        """
        생성자입니다.
        :param dsetdir: 카빙된 파일이 저장될 디렉토리입니다.
        :param image_file: 파일 카빙의 대상이 될 이미지 파일입니다.

        """

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
