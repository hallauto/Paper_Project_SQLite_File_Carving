import FileCarving
import FileConnector

image_file = r"F:\Android_x86_image\4월16일\sda1-10.dd"
print("Inputed image file. {0}".format(image_file))
logdump_file = r"F:\Android_x86_image\4월16일\logdump-sda1-10"
print("inputed logdump file {0}".format(logdump_file))
directory = r"F:\Android_x86_image\4월16일\carved"
print("Inputed directory for output {0}".format(directory))
block_size = 4096
print("Inputed block size. {0}".format(block_size))

if block_size is "":
    fileConnector = FileConnector.FileConnector(image_file)
else:
    fileConnector = FileConnector.FileConnector(image_file,int(block_size))

journal_Connector = FileConnector.FileConnector(logdump_file)

fileCarver = FileCarving.FileCarving(directory,fileConnector,journal_Connector)
fileCarver.parsing_journal()
fileCarver.carving_journaled_block()
print("{0}개의 저널된 블록에서 발견된 파일은 총 {1}개 입니다.".format(len(fileCarver.journal_parser.journal_results), fileCarver.file_many))
fileCarver.carving_rest_file()
fileCarver.report_end()