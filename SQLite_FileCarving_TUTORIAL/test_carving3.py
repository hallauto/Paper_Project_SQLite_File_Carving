import FileCarving
import FileConnector
from ExTCarving import EXTCarving, ExTJournalCarving

image_file = r"F:\Android_x86_image\4월15일\sda1.dd"
print("Inputed image file. {0}".format(image_file))
directory = r"F:\Android_x86_image\4월15일\carved"
print("Inputed directory for output {0}".format(directory))
block_size = 4096
print("Inputed block size. {0}".format(block_size))

if block_size is "":
    fileConnector = FileConnector.FileConnector(image_file)
else:
    fileConnector = FileConnector.FileConnector(image_file,int(block_size))

fileConnector.file_open(image_file)
result_file = open(directory + r"\result.txt",'w')

ext_carver = EXTCarving(fileConnector)
#EXT 저널을 먼저 확인합니다.
ext_carver.journal_carver.find_journal_superblock()
ext_carver.journal_carver.parse_journal_superblock()
ext_carver.journal_carver.find_journal_log()
result_file.write(ext_carver.journal_carver.print_journal_logs())
for journal_log in ext_carver.journal_carver.journal_log_list:
    ext_carver.journal_carver.find_sqlite_directory_entry(journal_log)
result_file.write(ext_carver.journal_carver.prints_whole_entry())

#EXT 저널의 확인이 완료되었습니다. 이제 EXT 수퍼블록을 확인합니다.
ext_carver.super_b_carver.find_superblock(ext_carver.journal_carver.journal_superblock_offset)
for ext_super_block in ext_carver.super_b_carver.ExTSuperBlock_list:
    ext_carver.super_b_carver.parsing_super_block(ext_super_block)
result_file.write(ext_carver.super_b_carver.print_whole_super_block())
ext_carver.super_b_carver.find_group_descriptor()
for ext_super_block in ext_carver.super_b_carver.ExTSuperBlock_list:
    ext_carver.super_b_carver.parsing_group_descriptor(ext_super_block)

result_file.write(ext_carver.super_b_carver.print_whole_group_descriptor())

file_carving = FileCarving(directory, fileConnector)
print('find is end')