import sys, os, sqlite3
if len(sys.argv) != 4:
	print >> sys.stderr,'SQLite3 Files Report\t\tMade by @ykx100\n\tUsage : python sqlite3_report.py [sourcedir] [result filename] [display sample rec#]\n\tExample : python sqlite3_report.py ./carved result.txt 5'
	exit(1)

basedir = sys.argv[1]
result_file = sys.argv[2]
samplenum = sys.argv[3]

wf = open(result_file,'w')

osfiles = os.listdir(basedir)
filecnt = 0
errfilecnt = 0
for filename in osfiles:
	result = ''
	try:
		dbfile = os.path.join(basedir, filename)
		sql3db = sqlite3.connect(dbfile)
		tmpcursor = sql3db.cursor()
		print "file opened : "+filename
		
		tmpcursor.execute("select name from sqlite_master where type = \'table\'")
		table_list = tmpcursor.fetchall()
		
		for i_tab in range(0,len(table_list)):
			tmpcursor.execute("select count(*) from "+table_list[i_tab][0])
			tablecount = tmpcursor.fetchall()[0][0]
			tmpcursor.execute("select sql from sqlite_master where name = \'"+table_list[i_tab][0]+"\'")
			sqlstr = tmpcursor.fetchall()
			wf.write(filename + " - " + table_list[i_tab][0] + " : " + str(tablecount)+" : "+str(sqlstr)+"\n")
			
			if tablecount <= 0: continue
			
			tmpcursor.execute("select * from "+table_list[i_tab][0]+ " limit 0,"+str(samplenum))
			table_line = tmpcursor.fetchall()
			
			if len(table_line)<=0: continue
			
			for i_line in range(0, len(table_line)):
				templine = ''
				for i_col in range(0, len(table_line[i_line])):
					if (type(table_line[i_line][i_col])==type(u'string')):
						col = table_line[i_line][i_col].encode('utf-8')
					else:
						col = str(table_line[i_line][i_col])
					if(col==''): col = 'null'
					col = col.replace("\n",'\t')
					templine = templine + "," + col
				wf.write("\t" + templine[1:] + "\n")
		filecnt = filecnt + 1
	except:
		print "\tError : Can't connect or execute query in "+filename
		errfilecnt = errfilecnt+1
print "==============================\ndone : "+str(filecnt)+" files reported"
print "error: "+str(errfilecnt)+" files"
wf.close()