#这是一个读取csv的简化版本

import pymysql
from functools import reduce
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap
from functools import partial
import sys
import csv



#建立倒排索引
#table每一行都是一个posting

#wfidf的倒排索引
f=open('wfidf.csv',encoding="UTF-8")
reader = csv.reader(f)
row=next(reader)
wf_table=[]
for row in reader:
    r=[row[1],[]]
    for j in range(2,len(row)):
        if float(row[j])>0:
            r[1].append([j-1,float(row[j])])
    wf_table.append(r)
f.close()

#tfidf的倒排索引
f=open('tfidf.csv',encoding="UTF-8")
reader = csv.reader(f)
row=next(reader)
tf_table=[]
for row in reader:
    r=[row[1],[]]
    for j in range(2,len(row)):
        if float(row[j])>0:
            r[1].append([j-1,float(row[j])])
    tf_table.append(r)
f.close()





#两个posting的AND操作
def AND(p1,p2):
    i=0
    j=0
    ans=[]
    while i<len(p1) and j<len(p2):
        if p1[i][0]==p2[j][0]:
            ans.append([p1[i][0],p1[i][1]+p2[j][1]])
            i=i+1
            j=j+1
        elif p1[i][0]<p2[j][0]:
            i=i+1
        else:
            j=j+1
    return ans
#两个posting的OR操作
def OR(p1,p2):
    i=0
    j=0
    ans=[]
    while i<len(p1) and j<len(p2):
        if p1[i][0]==p2[j][0]:
            ans.append([p1[i][0],p1[i][1]+p2[j][1]])
            i=i+1
            j=j+1
        elif p1[i][0]<p2[j][0]:
            ans.append(p1[i])
            i=i+1
        else:
            ans.append(p2[j])
            j=j+1
    while i<len(p1):
        ans.append(p1[i])
        i=i+1
    while j<len(p2):
        ans.append(p2[j])
        j=j+1
    return ans
#两个posting的ANDNOT操作
def ANDNOT(p1,p2):
    i=0
    j=0
    ans=[]
    while i<len(p1) and j<len(p2):
        if p1[i][0]==p2[j][0]:
            i=i+1
            j=j+1
        elif p1[i][0]<p2[j][0]:
            ans.append(p1[i])
            i=i+1
        else:
            j=j+1
    while i<len(p1):
        ans.append(p1[i])
        i=i+1
    return ans
#多个posting的AND操作
def AND_MU(plist):
    templist=sorted(plist,key=len)
    return reduce(AND,templist)
#多个posting的OR操作
def OR_MU(plist):
    templist=sorted(plist,key=len,reverse=True)
    return reduce(OR,templist)



'''
对term串的处理,即处理一行汉字的AND
返回一个posting
'''
def termsHandle(termlist,table):
    plist=[]
    for value in termlist:
        flag=False
        for row in table:
            if row[0]==value:
                plist.append(row[1])
                flag=True
        if flag==False:
            return []
    return AND_MU(plist)
'''
对常规搜索的支持，即只包含语句和空格的处理
'''
#辅助ranking函数
def nodeRanking(node):
    return node[1]
def oriSentence(sentence,table):
    sentence=sentence+" "
    tl=""
    plist=[]
    for c in sentence:
        if c!=" ":
            tl=tl+c
        else:
            if tl!="":
                plist.append(termsHandle(tl,table))
                tl=""
    posting=OR_MU(plist)
    return sorted(posting,key=nodeRanking,reverse=True)



'''
对布尔表达式子的支持，符号包括AND,OR,ANDNOT或&，|，-及括号(,)
'''
#改为标准表达式的辅助函数
def to_regularBool(sentence):
    s1=sentence.replace("ANDNOT","-")
    s2=s1.replace("AND","&")
    s3=s2.replace("OR","|")
    return s3
#转为前缀表达式
def to_suffix(sentence):
    stack=[]
    queue=[]
    tl=""
    for c in sentence:
        if c=="(":
            if(tl!=""):
                queue.append(tl)
                tl=""
            stack.append(c)
            continue
        elif c==")":
            if(tl!=""):
                queue.append(tl)
                tl=""
            while(stack[len(stack)-1]!="("):
                queue.append(stack[len(stack)-1])
                stack.pop()
            stack.pop()
            continue
        elif c=="&" or c=="|":
            if(tl!=""):
                queue.append(tl)
                tl=""
            if len(stack)==0:
                stack.append(c)
            elif stack[len(stack)-1]=="-" or stack[len(stack)-1]=="(":
                stack.append(c)
            else:
                while(len(stack)!=0 and stack[len(stack)-1]!="-" and stack[len(stack)-1]!="("):
                    queue.append(stack[len(stack)-1])
                    stack.pop()
                stack.append(c)
        elif c=="-":
            if(tl!=""):
                queue.append(tl)
                tl=""
            while(len(stack)!=0 and stack[len(stack)-1]!="("):
                    queue.append(stack[len(stack)-1])
                    stack.pop()
            stack.append(c)
        else:
            tl=tl+c
    if(tl!=""):
        queue.append(tl)
    while(len(stack)!=0):
        queue.append(stack[len(stack)-1])
        stack.pop()
    return queue
#整合布尔表达式的计算
def boolSentence(sentence,table):
    sentence=to_regularBool(sentence)
    sentence=to_suffix(sentence)
    for i in range(len(sentence)):
        value=sentence[i]
        if value!="&" and value!="|" and value!="-":
            sentence[i]=termsHandle(value,table)
    stack=[]
    for c in sentence:
        if c=="&":
            r=stack[-1]
            stack.pop()
            l=stack[-1]
            stack.pop()
            stack.append(AND(l,r))
        elif c=="|":
            r=stack[-1]
            stack.pop()
            l=stack[-1]
            stack.pop()
            stack.append(OR(l,r))
        elif c=="-":
            r=stack[-1]
            stack.pop()
            l=stack[-1]
            stack.pop()
            stack.append(ANDNOT(l,r))
        else:
            stack.append(c)
    return sorted(stack[0],key=nodeRanking,reverse=True)

'''
向量模型相关
'''





'''
ui界面相关
'''
#ui的类
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 700)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setGeometry(QtCore.QRect(100, 70, 450, 41))
        self.lineEdit.setObjectName("lineEdit")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(20, 80, 71, 21))
        self.label.setObjectName("label")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(450,70, 100, 41))
        self.pushButton.setObjectName("pushButton")
        self.listWidget = QtWidgets.QListWidget(self.centralwidget)
        self.listWidget.setGeometry(QtCore.QRect(100, 120, 600, 500))
        self.listWidget.setObjectName("listWidget")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(20, 130, 71, 21))
        self.label_2.setObjectName("label_2")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 552, 22))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menubar.addAction(self.menu.menuAction())

        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(550,-70, 300, 400))
        self.label_3.setObjectName("label_3")
        pix = QPixmap('logo.png')
        self.label_3.setPixmap(pix)

    

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label.setText(_translate("MainWindow", "搜索内容"))
        self.pushButton.setText(_translate("MainWindow", "搜索"))
        self.label_2.setText(_translate("MainWindow", "搜索结果"))
        self.menu.setTitle(_translate("MainWindow", "搜索界面"))
#显示函数
def convert(ui,table):
        ui.listWidget.clear()
        input = ui.lineEdit.text()
        flag=False
        for value in input:
            if value=="&" or value=="|" or value=="-" or value=="(" or value==")" or "A" in value or "O" in value:
                flag=True
        if flag:
            posting=boolSentence(input,table)
        else:
            posting=oriSentence(input,table)
        if len(posting)==0:
            ui.listWidget.addItem("未检索到相应结果")
            return
        for node in posting:
            no=node[0]
            f=open('songci\Doc'+str(no)+'.txt','r')
            txt=f.read()
            result="Doc"+str(no)+"\n"+"score:"+str(node[1])+"\n"
            timer=0
            for c in txt:
                timer=timer+1
                if timer==37:
                    result=result+"\n"
                    timer=0
                if c in input and c!=" ":
                    result=result+"["+c+"]"
                else:
                    result=result+c
            ui.listWidget.addItem(result)

#界面启动
app = QtWidgets.QApplication(sys.argv)  
MainWindow = QtWidgets.QMainWindow()   
ui = Ui_MainWindow()                         
ui.setupUi(MainWindow)                 
MainWindow.show()                  
ui.pushButton.clicked.connect(partial(convert,ui,tf_table))  
sys.exit(app.exec_())            