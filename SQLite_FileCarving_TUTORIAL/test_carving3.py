import FileCarving
import FileConnector
from ExTCarving import EXTCarving

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
ExTCarver.find_journal_superblock()
ExTCarver.find_superblock()
print('find is end')