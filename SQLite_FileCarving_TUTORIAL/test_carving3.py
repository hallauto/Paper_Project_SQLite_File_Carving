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

ExTCarver = EXTCarving(fileConnector)
ExTCarver.journal_carver.find_journal_superblock()
ExTCarver.journal_carver.parse_journal_superblock()
ExTCarver.find_superblock()
for index in range(len(ExTCarver.superblock_number_list)):
    ExTCarver.parsing_super_block(index)
ExTCarver.find_group_descriptor()
ExTCarver.journal_carver.find_journal_log()
print('find is end')