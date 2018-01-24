import re
from enum import IntEnum


class Journal_type(IntEnum):
    Descriptor = 1
    Block_Commit = 2
    Journal_v1 = 3
    Journal_v2 = 4
    revocation = 5


def parse_text(input_text):
    original_text = input_text
    journal_sequence = []
    journal_info = {}
    if ('transsaction' in original_text):
        (journal_start_block, transaction_number) = parse_journal_head(original_text)

    # 먼저 저널링 순서를 나타내는 문장을 파싱합니다. 이를 위해 앞 부분 문장을 제거합니다.
    trimmed_text1 = original_text.strip('Found expected sequence ')
    journal_sequence_parser = re.compile(r'\d+|\([^()]+\)')
    parser_result = journal_sequence_parser.findall(trimmed_text1)
    journal_sequence.append(parser_result[0])
    journal_type = parser_result[1]
    journal_type_name = Journal_type(journal_type).name

    print('해당 저널은 {0}에서 {1}까지 작동합니다'.format(journal_start_block, transaction_number))

    i = 0
    while (i < journal_sequence.__len__()):
        print('저널 {0}번은 {1} 타입의 {2}번 블록을 가리킵니다.'.format(journal_sequence[i], journal_type_name[i]))
        i += 1


def parse_journal_head(input_text):
    original_text = input_text
    journal_head_parser = re.compile(r'\d+')
    parser_result = journal_head_parser.findall(original_text)
    journal_start_block = parser_result[0]
    transaction_number = parser_result[1]

    return journal_start_block, transaction_number
