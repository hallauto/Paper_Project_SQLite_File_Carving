""" SQLite file carving을 위한 프로그램 제작.
    그 첫번째는 기존에 있던 SQLite file carving 코드를 분석, 연구해서
    SQLite file carving의 시그니처 기반 카빙을 만드는 것입니다. """

import sys,os,re,JournalParsing
class FileConnector:
    """ 기존 파일은 다양한 파일시스템에서 사용 가능하지 못할듯 합니다.
        특히 전체 디스크 이미지를 분석하는 경우 같은 특이 사항을 대비한 코드가 필요합니다.
        해당 사항을 적용해야합니다.
    """
    def __init__(self, FileName):
        srcName = FileName
        self.parser = ''
        if FileName.contain(".journal"):
            self.file_type = 'journal'
            self.fileConnector = JournalParsing.FileConnector(FileName)
        elif FileName.contain(".dd"):
            self.file_type = 'dd'
        elif FileName.contain(".image"):
            self.file_type = 'image'

        try:
            self.file = open(FileName)
        except IOError as error:
            print("파일이 존재하지않습니다.")
        except Exception as error:
            print("An exception happened: " + str(error))


class SQLiteCarvingByJournal:

    def __init__(self, journal_file_name, image_file):
        image_connector = FileConnector(image_file)