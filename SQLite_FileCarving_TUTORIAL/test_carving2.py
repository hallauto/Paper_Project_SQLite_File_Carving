import FileCarving
import FileConnector
import time

journaled = True
report_on = True

start_time = time.time()
image_file = r"G:\Kimchangyu\Test4\30GB\sda1-30.dd"
print("Inputed image file. {0}".format(image_file))
directory = r"G:\Kimchangyu\Test4\30GB\carved-journal"
print("Inputed directory for output {0}".format(directory))
block_size = 4096
print("Inputed block size. {0}".format(block_size))

if block_size is "":
    fileConnector = FileConnector.FileConnector(image_file)
else:
    fileConnector = FileConnector.FileConnector(image_file,int(block_size))

fileConnector.file_open(image_file)
fileCarver = FileCarving.FileCarving(directory,fileConnector,start_time)

if report_on is True:
    fileCarver.report_on()

if journaled is True:
    fileCarver.ExT_Parsing()
    fileCarver.check_journaled_block()
    fileCarver.carving_journaled_block()
else:
    fileCarver.carving_whole_file()

if report_on is True:
    fileCarver.report_end()
print("start_time ", start_time, time.time())
print("--- %s seconds ---" %(time.time() - start_time))