

class JournalParser:
    def __init__(self, JournalFile):
        self.journal_file = JournalFile
        self.parse_text1 = ""
        self.parse_text2 = ""
        self.tokenizer = ""
        self.whole_work = False
        self.while_work_journal = ""
        self.currentJournal = ""
        self.current_work = ""

    def reset_status(self):
        if (self.journal_file):
            self.whole_work = False
            self.while_work_journal = False
            self.currentJournal = ""
            self.current_work = ""
            self.current_jornal = ""


    def readNextJournal(self):
        if (self.while_work_journal != True):
            print('work is not over!')
            return
        try:
            self.currentJournal = self.journal_fie.readLine()
        except EOFError as err:
            print("journal File is end!")
            whole_work = True #파일의 끝을 확인 했으므로 모든 작업 종료
        else:
            print("read {0} journal:{1}".format(self.current_work, self.currentJournal))
                
        

    def trimJournalText(self,tokenizer=''):
        if (self.tokenizer != tokenizer):
            self.tokenizer = tokenizer


    def current_work_print(self):
        print("총 {0}개의 저널중 {1}번째 저널 확인중".format(self.whole_journal, self.current_work))

            
        
