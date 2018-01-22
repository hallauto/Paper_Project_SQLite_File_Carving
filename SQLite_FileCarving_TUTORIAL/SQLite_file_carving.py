""" SQLite file carving을 위한 프로그램 제작.
    그 첫번째는 기존에 있던 SQLite file carving 코드를 분석, 연구해서
    SQLite file carving의 시그니처 기반 카빙을 만드는 것입니다. """

import sys,os,re
class FileConnector:
    """ 기존 파일은 다양한 파일시스템에서 사용 가능하지 못할듯 합니다.
        특히 전체 디스크 이미지를 분석하는 경우 같은 특이 사항을 대비한 코드가 필요합니다.
        해당 사항을 빨리 적용해야합니다.
        """
    
def __init__(self, FileName):
    srcName = FileName
    if (FileName.contain(".journal")):
        filetype = 'journal'
    elif (FileName.contain(".dd")):
        filetype = 'dd'
    elif (FileName.contain(".image")):
        filetype = 'image'

    try:
        file = open(FileName)
    except Exception as error:
        print("An exception happened: " + str(error))

