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

ExTCarver = EXTCarving(fileConnector)
ExTCarver.journal_carver.find_journal_superblock()
ExTCarver.journal_carver.parse_journal_superblock()
ExTCarver.find_superblock()
for ext_super_block in ExTCarver.ExTSuperBlock_list:
    ExTCarver.parsing_super_block(ext_super_block)
result_file.write(ExTCarver.print_whole_super_block())
ExTCarver.find_group_descriptor()
ExTCarver.journal_carver.find_journal_log()
result_file.write(ExTCarver.journal_carver.print_journal_logs())
for journal_log in ExTCarver.journal_carver.journal_log_list:
    ExTCarver.journal_carver.find_sqlite_directory_entry(journal_log)
result_file.write(ExTCarver.journal_carver.prints_whole_entry())
for ext_super_block in ExTCarver.ExTSuperBlock_list:
    ExTCarver.parsing_group_descriptor(ext_super_block)

result_file.write(ExTCarver.print_whole_group_descriptor())

print('find is end')