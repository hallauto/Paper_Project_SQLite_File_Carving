import sys, os

if len(sys.argv) != 3:
    print(
        'SQLite3 Continuous Files carver\t\tmade by @ykx100\n\tUsage : sqlite3j_carver.py [sourcefile] [destdir]\n\tExample : python sqlite3j_carver.py dumped.dat ./carved')
    exit(1)

srcfile = sys.argv[1]
destdir = sys.argv[2]

rf = open(srcfile, 'rb')
rblock = 'start'
sql3_j_header = 'd9d505f920a163d7'.encode('hex')

filecnt = 0
while (len(rblock) > 1):
    rblock = rf.read(512)
    header_offset = rblock.find(sql3_j_header.encode('UTF-8'))

    if (header_offset <= -1):
        continue
    print(str(hex(rf.tell())) + "헤더 오프셋이 있습니다. 즉, 이 블록에 SQLite 파일이 존재합니다.")
    rf.seek(-1 * (512 - header_offset), 1)
    rblock = rf.read(512)

    print("rblcok[21] = " + str(rblock[21]))
    if (rblock[21] != 64 and rblock[22] != 32 and rblock[23] != 32):
        print(str(hex(rf.tell() - 512)) + "...그러나 파일은 없네요.")
        continue

    psize = (rblock[16] * 256 + rblock[17])
    print("psize = " + str(psize))
    if (psize <= -1):
        continue
    rblock = rblock + rf.read(psize - 512)

    filename = "carved_" + str(rf.tell()) + ".sqlite3"
    wfname = os.path.join(destdir, filename)
    print("write file : " + wfname)
    wf = open(wfname, 'wb')
    wf.write(rblock)

    while (len(rblock) > 1):
        rblock = rf.read(psize)
        if ((rblock[0] != '\x00') and (rblock[0] != '\x0D') and (rblock[0] != '\x0A') and (rblock[0] != '\x05') and (
                rblock[0] != '\x02')):
            break
        if ((ord(rblock[1]) * 256 + ord(rblock[2]) > psize) or (ord(rblock[5]) * 256 + ord(rblock[6]) > psize)):
            break
        wf.write(rblock)
    wf.close()
    filecnt = filecnt + 1

print("==============================\ndone: " + str(filecnt) + " files carved")
rf.close()
