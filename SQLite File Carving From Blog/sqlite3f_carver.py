import sys, os
if len(sys.argv) != 3:
	print >> sys.stderr,'SQLite3 Continuous Files carver\t\tmade by @ykx100\n\tUsage : sqlite3f_carver.py [sourcefile] [destdir]\n\tExample : python sqlite3f_carver.py dumped.dat ./carved'
	exit(1)

srcfile = sys.argv[1]
destdir = sys.argv[2]

rf = file(srcfile,'rb')
rblock = 'start'
sql3header = 'SQLite format 3\x00'

filecnt = 0
while (len(rblock) > 1):
	rblock = rf.read(512)
	header_offset = rblock.find(sql3header)
	
	if (header_offset<=-1):
		continue
	
	rf.seek(-1*(512-header_offset), 1)
	rblock = rf.read(512)
	
	if( rblock[21] != '\x40' and rblock[22] != '\x20' and rblock[23] != '\x20'):
		continue
	
	psize = (ord(rblock[16])*256 + ord(rblock[17]))
	rblock = rblock + rf.read(psize-512)
	
	filename = "carved_"+str(rf.tell())+".sqlite3"
	wfname = os.path.join(destdir, filename)
	print("write file : "+wfname)
	wf = file(wfname,'wb')
	wf.write(rblock)
	
	while (len(rblock) > 1):
		rblock = rf.read(psize)
		if ( (rblock[0] != '\x00') and (rblock[0] != '\x0D') and (rblock[0] != '\x0A') and (rblock[0] != '\x05') and (rblock[0] != '\x02') ):
			break
		if ( (ord(rblock[1])*256+ord(rblock[2]) > psize) or (ord(rblock[5])*256+ord(rblock[6]) > psize) ):
			break
		wf.write(rblock)
	wf.close()
	filecnt = filecnt+1

print "==============================\ndone: "+str(filecnt)+" files carved"
rf.close()
