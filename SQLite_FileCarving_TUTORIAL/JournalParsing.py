import re
from enum import IntEnum


class JournalTypeEnum(IntEnum):
    Descriptor = 1
    Block_Commit = 2
    Journal_v1 = 3
    Journal_v2 = 4
    revocation = 5

class JournalParser:
    def __init__(self):
        self.journal_start_block = 0
        self.transaction_number = 0

        self.journal_sequence = 0
        self.journal_type = 0
        self.journal_type_name = ""

    def parse_journal_head(self, input_text):
        original_text = input_text
        journal_head_parser = re.compile(r'\d+')
        parser_result = journal_head_parser.findall(original_text)
        journal_start_block = parser_result[0]
        transaction_number = parser_result[1]

        return journal_start_block, transaction_number

    def parse_one_line(self, input_text):
        original_text = input_text
        journal_info = {}
        if input_text is '':
            return
        if 'transaction' in original_text:
            (journal_start_block, transaction_number) = self.parse_journal_head(original_text)
            print('해당 저널은 {0}번 블록에서 시작하며,  {1}개수의 트랜잭션을 저널링했습니다.'.format(journal_start_block, transaction_number))
            return
        if 'end of journal' in original_text:
            # (end_transaction_number, journal_end_block) = parse_journal_tale(original_text)
            return

        # 먼저 저널링 순서를 나타내는 문장을 파싱합니다. 이를 위해 앞 부분 문장을 제거합니다.
        trimmed_text1 = original_text.strip('Found expected sequence')
        journal_sequence_parser = re.compile(r'\d+')
        parser_result = journal_sequence_parser.findall(trimmed_text1)
        print(parser_result)
        self.journal_sequence = parser_result[0]
        self.journal_type = parser_result[1]
        self.journal_type_name = JournalTypeEnum(int(self.journal_type)).name

        print('저널 {0}번은 {1} 타입의 {2}번 블록을 가리킵니다.'.format(self.journal_sequence, self.journal_type_name, parser_result[2]))