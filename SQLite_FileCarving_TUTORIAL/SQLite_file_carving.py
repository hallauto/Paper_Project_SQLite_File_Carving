""" SQLite file carving을 위한 프로그램 제작.
    그 첫번째는 기존에 있던 SQLite file carving 코드를 분석, 연구해서
    SQLite file carving의 시그니처 기반 카빙을 만드는 것입니다. """

import JournalParsing, FileConnector


class SQLiteCarvingByJournal:
    """ 전체 워크 플로우를 담당하는 클래스입니다. 이 클래스가 각각의 다른 클래스를 멤버 변수로서 관리합니다.
        해당 저널 파일과 이미지 파일을 각각의 FileConnector 오브젝트로 관리합니다.
    """

    def __init__(self, journal_file_name, image_file):
        self.image_connector = FileConnector(image_file)
        self.journal_connector = FileConnector(journal_file_name)
        self.journal_parser = JournalParsing.JournalParser()

    def parse_whole_file(self):
        self.journal_parser.parse_whole_file(self.journal_connector.file)

    def parse_whole_text(self):
        self.journal_parser.parse_whole_text(self.journal_connector.file.readlines())

    def parse_one_line(self):
        try:
            self.journal_parser.parse_one_line(self.journal_connector.file.readline())
        except IOError:
            print("저널 읽기 중 에러 발생")


test = SQLiteCarvingByJournal("logdump1.txt", "")
test.parse_whole_file()
