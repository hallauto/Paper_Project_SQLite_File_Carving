import FileCarving
import FileConnector

print("Input image file.")
image_file = input()
print("input logdump file")
logdump_file = input()
print("Input directory for output")
directory = input()
print("Input block size. If don't type, then use default = 4096")
block_size = input()

if block_size is "":
    fileConnector = FileConnector.FileConnector(image_file)
else:
    fileConnector = FileConnector.FileConnector(image_file,int(block_size))

journal_Connector = FileConnector.FileConnector(logdump_file)

fileCarver = FileCarving.FileCarving(directory,fileConnector,journal_Connector)
fileCarver.parsing_journal()
fileCarver.carving_journaled_block()
print("{0}개의 저널된 블록에서 발견된 파일은 총 {1}개 입니다.".format(fileCarver.journal_parser.transaction_number, fileCarver.file_many))
fileCarver.carving_whole_file()
