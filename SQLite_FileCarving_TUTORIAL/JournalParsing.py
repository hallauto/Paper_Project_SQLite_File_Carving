import re

def parse_text(input_text):
    original_text = input_text
    if ('transsaction' in original_text):
        parse_journal_head(original_text)

    #먼저 저널링 순서를 나타내는 문장을 파싱합니다. 이를 위해 앞 부분 문장을 제거합니다.
    trimmed_text1 = original_text.strip('Found expected sequence ')
    journal_sequence_parser = re.compile(r'\d+|\([^()]+\)')
    parser_result = journal_sequence_parser.findall(trimmed_text1)
    journal_sequence = parser_result[0]
    journal_type = parser_result[1]
    journal_type_name =parser_result[2].strip('(').strip(')')

    
def parse_journal_head(input_text):
    original_text = input_text
    journal_head_parser = re.compile(r'^\d+')
    parser_result = journal_head_parser.search(original_text)
    journal_start_block = parser_result.group(1)
    transaction_number = parser_result.group(2)

