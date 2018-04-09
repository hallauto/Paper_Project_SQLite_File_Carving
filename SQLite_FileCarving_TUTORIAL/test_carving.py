import FileCarving
import FileConnector

print("Input image file.")
image_file = input()
print("Input directory for output")
directory = input()
print("Input block size. If don't type, then use default = 4096")
block_size = input()

if block_size is "":
    fileConnector = FileConnector.FileConnector(image_file)
else:
    fileConnector = FileConnector.FileConnector(image_file,int(block_size))

fileCarver = FileCarving.FileCarving(directory,fileConnector)
fileCarver.carving_whole_file()
