import pymysql
from openpyxl import Workbook
import math

#tf到wf的函数
def wf(n):
    if n==0:
        return 0
    else:
        return 1+math.log10(n)

#读入所有汉字形成字典字符串
txt=""
tempt=""
txtTable=[]
no=1
while no<=270:
    f=open('songciDep\Doc'+str(no)+'.txt','r')
    tempt=f.read()
    txt=txt+tempt
    txtTable.append(tempt)
    f.close()
    no=no+1
charSet=set([])
for i in range(len(txt)):
    charSet.add(txt[i])
charSet.remove(" ")
charList=""
for key in charSet:
    charList=charList+key

#连接for_practice数据库
conn=pymysql.connect(host = "localhost",user = "root",passwd = "xxxxxxxxxxx",db = "for_practice")
#创建游标
cur=conn.cursor()
#填写数据库表的内容
boolsql="replace into boolMatrix values%s"
countsql="replace into countMatrix values%s"
tfidfsql="replace into tfidf values%s"
wfidfsql="replace into wfidf values%s"
for i in range(len(charList)):
    tempList1=[i+1,charList[i]]
    tempList2=[i+1,charList[i]]
    tempList3=[i+1,charList[i]]
    tempList4=[i+1,charList[i]]
    for j in range(270):
        if txtTable[j].count(charList[i])==0:
            tempList1.append(0)
        else:
            tempList1.append(1)
        tempList2.append(txtTable[j].count(charList[i]))
    idf=math.log10(270/sum(tempList1[2:len(tempList1)]))
    for value in tempList2[2:len(tempList2)]:
        tempList3.append(value*idf)
        tempList4.append(wf(value)*idf)
    cur.execute(boolsql%str(tuple(tempList1)))
    cur.execute(countsql%str(tuple(tempList2)))
    cur.execute(tfidfsql%str(tuple(tempList3)))
    cur.execute(wfidfsql%str(tuple(tempList4)))
print("数据表填写完成")

cur.close()#关闭游标
conn.commit()#提交修改
conn.close()#再关闭数据库连接

