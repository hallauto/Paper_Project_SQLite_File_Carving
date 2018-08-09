import FileCarving
import FileConnector
import ExTCarving

image_file = r"F:\Android_x86_image\4월16일\sda1-10.dd"
print("Inputed image file. {0}".format(image_file))
result_file = r"F:\Android_x86_image\4월16일\result.txt"
print("inputed result file {0}".format(result_file))
directory = r"F:\Android_x86_image\4월16일\carved"
print("Inputed directory for output {0}".format(directory))
block_size = 4096
print("Inputed block size. {0}".format(block_size))

if block_size is "":
    fileConnector = FileConnector.FileConnector(image_file)
else:
    fileConnector = FileConnector.FileConnector(image_file,int(block_size))

result_fileConnector = FileConnector.FileConnector(result_file)
fileConnector.file_open(image_file)
fileCarver = FileCarving.FileCarving(directory,fileConnector, result_fileConnector)
fileCarver.ExT_Parsing()
fileCarver.check_journaled_block()
fileCarver.carving_journaled_block()
#print("{0}개의 저널된 블록에서 발견된 파일은 총 {1}개 입니다.".format(len(fileCarver.journal_parser.journal_results), fileCarver.file_many))
fileCarver.carving_rest_file()
fileCarver.report_end()