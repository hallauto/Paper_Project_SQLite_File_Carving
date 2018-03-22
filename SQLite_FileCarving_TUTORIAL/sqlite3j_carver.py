import sys
import os
import struct

if len(sys.argv) != 3:
    print(
        'SQLite3 Continuous Files carver\t\tmade by @ykx100\n\tUsage : sqlite3j_carver.py [sourcefile] [destdir]\n\tExample : python sqlite3j_carver.py dumped.dat ./carved')
    exit(1)

srcfile = sys.argv[1]
destdir = sys.argv[2]

rf = open(srcfile, 'rb')
rblock = 'start'
sql3_j_header = b'\xd9\xd5\x05\xf9 \xa1c\xd7'

filecnt = 0
while (len(rblock) > 1):
    rblock = rf.read(512)
    header_offset = rblock.find(sql3_j_header)

    if (header_offset <= -1):
        continue
    print(str(hex(rf.tell())) + " 헤더 오프셋 {0}이 있습니다. 즉, 이 블록에 SQLite 저널 파일이 존재합니다.".format(header_offset))
    rf.seek(-1 * (512 - header_offset), 1)
    rblock = rf.read(512)

    try:
        page_count = struct.unpack('L', bytearray(rblock[8:12]))[0]
        print("rblcok[8] : The number of pages in the next segment of the journal = " + str(page_count))
        checksum = struct.unpack('L',bytearray(rblock[12:16]))[0]
        print("rblcok[12] : A random nonce for the checksum = " + str(checksum))
        initial_db_size = struct.unpack('L',bytearray(rblock[16:20]))[0]
        print("rblcok[16] : Initial size of the database in pages = " + str(initial_db_size))
        sector_size = struct.unpack('L',bytearray(rblock[20:24]))[0]
        print("rblcok[20] : Size of a disk sector assumed by the process that wrote this journal = " + str(sector_size))
        page_size = struct.unpack('L',bytearray(rblock[24:28]))[0]
        print("rblcok[24] : Size of pages in this journal = " + str(page_size))

    except ValueError:
        continue

    if initial_db_size <= 0:
        print("error : initial_page_size = [0]".format(initial_db_size),)
        continue
    if sector_size <= 0:
        print("error : sector_size = [0]".format(sector_size),)
        continue
    if page_size <= 0:
        print("error : page_size = [0]".format(page_size),)
        continue

    #SQLite 저널파일은 헤더 이후에는 섹터 크기만큼의 빈 자리를 둡니다. 이유는 섹터 단위로 쓰기가 이루어지는중, 이후의 데이터가 오류나 실패로 변질되는 것을 막기 위함입니다.
    rf.seek(-1 * 512, 1)
    rblock = rf.read(sector_size)

    filename = "carved_" + str(rf.tell()) + ".db-journal"
    wfname = os.path.join(destdir, filename)
    print("write file : " + wfname)
    wf = open(wfname, 'wb')
    wf.write(rblock)

    while (len(rblock) > 3):
        rblock = rf.read(page_size)
        #페이지 번호가 0 이하일 수는 없습니다.
        try:
            if struct.unpack('L',bytearray(rblock[0:4]))[0] <= 0:
                break
        except ValueError:
            break
        wf.write(rblock)
    wf.close()
    filecnt = filecnt + 1

print("==============================\ndone: " + str(filecnt) + " files carved")
rf.close()
