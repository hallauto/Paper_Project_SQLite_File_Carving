import sys,os

class FileConnector:
    """ 기존 파일은 다양한 파일시스템에서 사용 가능하지 못할듯 합니다.
        특히 전체 디스크 이미지를 분석하는 경우 같은 특이 사항을 대비한 코드가 필요합니다.
        해당 사항을 적용해야합니다.
    """
    def __init__(self, FileName, block_size = 0):
        srcName = FileName
        self.parser = ''
        if FileName.find(".journal") or FileName.find("logdump"):
            self.file_type = 'journal'
        elif FileName.find(".dd"):
            self.file_type = 'dd'
            self.block_size = block_size
        elif FileName.find(".image"):
            self.file_type = 'image'
            self.block_size = block_size

        try:
            self.file = open(FileName)
        except IOError as error:
            print("파일이 존재하지않습니다.")
        except Exception as error:
            print("An exception happened: " + str(error))

    def reset_file_read(self):
        self.file.seek(0)

    def change_block_file_read(self, block_number):
        try:
            self.file.seek(block_number * self.block_size,0)
            if self.file.readable() is False:
                print("There isn't block number {0}".format(block_number))

            self.file.read(self.block_size)
        except IOError as error:
            print("There isn't block number {0}")


