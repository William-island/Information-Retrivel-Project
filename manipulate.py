import pymysql
from functools import reduce
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap
from functools import partial
import sys
import math
import time
import copy


#连接数据库
conn=pymysql.connect(host = "localhost",user = "root",passwd = "xxxxxxxxxxxx",db = "for_practice")
#创建游标
cur=conn.cursor()

#建立倒排索引
#table每一行都是一个posting


#wfidf的倒排索引
cur.execute("select * from wfidf")
wf_table=[]
hanlist=[]
for row in cur.fetchall():
    r=[row[1],[]]
    hanlist.append(row[1])
    for j in range(2,len(row)):
        if row[j]>0:
            r[1].append([j-1,row[j]])
    wf_table.append(r)


#求第二范式函数
def norm(doc):
    sum=0
    for value in doc:
        sum=sum+value*value
    return sum**0.5
#计算一行的idf
def df_cal(row):
    s=0
    for i in range(2,272):
        if row[i]!=0:
            s=s+1
    return s
#读入countmatrix，形成doc向量
#采用平方和的方法归一化
cur.execute("select * from countmatrix")
docs=[]
df=[]
sum_N=0 #统计所有文档的总字数
for i in range(270):
    docs.append([])
for row in cur.fetchall():
    df.append(df_cal(row))
    for i in range(2,272):
        docs[i-2].append(row[i])
        sum_N=sum_N+row[i]
idf=[]
for i in range(len(df)):
    idf.append(math.log10(270/df[i]))
dfN=[]  #计算term项的在所有文档中的概率
for i in range(len(df)):
    dfN.append(df[i]/sum_N)
max_docs=copy.deepcopy(docs) #采用最大值归一化方法
norm_docs=copy.deepcopy(docs) #采用平方归一化方法
for k in range(len(norm_docs)):
    under=norm(norm_docs[k])
    for i in range(len(norm_docs[k])):
        norm_docs[k][i]=norm_docs[k][i]*idf[i]/under
norm_docs[0][0]=8
for k in range(len(max_docs)):
    under=max(max_docs[k])
    for i in range(len(max_docs[k])):
        max_docs[k][i]=max_docs[k][i]*idf[i]/under







'''
布尔模型相关
'''
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
#将查询请求改为加权向量形式
def to_vector(sentence,hanlist,idf):
    vector_q=[]
    for han in hanlist:
        vector_q.append(sentence.count(han))
    under=norm(vector_q)
    if under==0:
        return vector_q
    for i in range(len(vector_q)):
        vector_q[i]=vector_q[i]*idf[i]/under
    return vector_q
#计算两个向量间的距离
def vec_distance(v1,v2):
    sums=0
    for i in range(len(v1)):
        sums=sums+v1[i]*v2[i]
    return sums
#计算所有文档和查询的距离，返回文档编号-距离矩阵（已排序）
def distances(docs,vq):
    d=[]
    for i in range(len(docs)):
        d.append([i+1,vec_distance(docs[i],vq)])
    return sorted(d,key=nodeRanking,reverse=True)
#考虑非零元素的简化算法
def simplified_distances(docs,vq):
    d=[]
    for i in range(1,271):
        d.append([i,0])
    for i in range(len(vq)):
        if vq[i]!=0:
            for j in range(270):
                if docs[j][i]!=0:
                    d[j][1]=d[j][1]+docs[j][i]*vq[i]
    return sorted(d,key=nodeRanking,reverse=True)


'''
概率模型相关
'''
#计算ri
r=[]
for i in range(len(df)):
    if df[i]!=270:
        r.append(df[i]/270)
    else:
        r.append(0.00000000000000000000000000001)
#给出pi
p=[]
for i in range(len(df)):
    p.append(0.5)
#pi的第二种方法
p2=[]
for i in range(len(df)):
    p.append((df[i]+0.5)/271)
#计算ci的函数
def c_cal(r,p):
    c=[]
    for i in range(len(r)):
        print(p[i],r[i])
        c.append(math.log10(p[i]*(1-r[i])/((1-p[i])*r[i])))
    return c
c=c_cal(r,p)
#把查询语句变为01向量
def to_01vector(sentence,hanlist):
    vector_q=[]
    for han in hanlist:
        if sentence.count(han)!=0:
            vector_q.append(1)
        else:
            vector_q.append(0)
    return vector_q
#根据查询计算每篇doc的RSV并排序
def RSV_ranking(docs,qv,c):
    RSVs=[]
    for i in range(1,271):
        RSVs.append([i,0])
    for i in range(len(qv)):
        if qv[i]!=0:
            for j in range(270):
                if docs[j][i]!=0:
                    RSVs[j][1]=RSVs[j][1]+c[i]
    return sorted(RSVs,key=nodeRanking,reverse=True)


'''
语言模型相关
'''
#语言模型排序函数
def MLE_ranking(docs,qv,lamb,dfN):
    dposting=[]
    for i in range(1,271):
        dposting.append([i,1])
    ff=False
    for i in range(len(qv)):
        if qv[i]!=0:
            if ff==False:
                ff=True
            for j in range(270):
                dposting[j][1]=dposting[j][1]*(lamb*docs[j][i]+(1-lamb)*dfN[i])
    if ff==False:
        for i in range(270):
            dposting[i][1]=0
    return sorted(dposting,key=nodeRanking,reverse=True)


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
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(0, 0, 1000, 1000))
        self.tabWidget.setMaximumSize(QtCore.QSize(800, 16777215))
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.lineEdit = QtWidgets.QLineEdit(self.tab)
        self.lineEdit.setGeometry(QtCore.QRect(100,70, 450, 41))
        self.lineEdit.setObjectName("lineEdit")
        self.pushButton = QtWidgets.QPushButton(self.tab)
        self.pushButton.setGeometry(QtCore.QRect(450,70, 100, 41))
        self.pushButton.setObjectName("pushButton")
        self.label = QtWidgets.QLabel(self.tab)
        self.label.setGeometry(QtCore.QRect(15, 60, 70, 40))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.tab)
        self.label_2.setGeometry(QtCore.QRect(15, 125, 70, 40))
        self.label_2.setObjectName("label_2")
        self.listWidget = QtWidgets.QListWidget(self.tab)
        self.listWidget.setGeometry(QtCore.QRect(100, 120, 615, 500))
        self.listWidget.setObjectName("listWidget")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.label_3 = QtWidgets.QLabel(self.tab_2)
        self.label_3.setGeometry(QtCore.QRect(15, 60, 70, 40))
        self.label_3.setObjectName("label_3")
        self.lineEdit_2 = QtWidgets.QLineEdit(self.tab_2)
        self.lineEdit_2.setGeometry(QtCore.QRect(100,70, 450, 41))
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.pushButton_2 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_2.setGeometry(QtCore.QRect(450,70, 100, 41))
        self.pushButton_2.setObjectName("pushButton_2")
        self.label_4 = QtWidgets.QLabel(self.tab_2)
        self.label_4.setGeometry(QtCore.QRect(15, 125, 70, 40))
        self.label_4.setObjectName("label_4")
        self.listWidget_2 = QtWidgets.QListWidget(self.tab_2)
        self.listWidget_2.setGeometry(QtCore.QRect(100, 120, 615, 500))
        self.listWidget_2.setObjectName("listWidget_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.label_5 = QtWidgets.QLabel(self.tab_3)
        self.label_5.setGeometry(QtCore.QRect(15, 60, 70, 40))
        self.label_5.setObjectName("label_5")
        self.lineEdit_3 = QtWidgets.QLineEdit(self.tab_3)
        self.lineEdit_3.setGeometry(QtCore.QRect(100,70, 450, 41))
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.pushButton_3 = QtWidgets.QPushButton(self.tab_3)
        self.pushButton_3.setGeometry(QtCore.QRect(450,70, 100, 41))
        self.pushButton_3.setObjectName("pushButton_3")
        self.label_6 = QtWidgets.QLabel(self.tab_3)
        self.label_6.setGeometry(QtCore.QRect(15, 125, 70, 40))
        self.label_6.setObjectName("label_6")
        self.listWidget_3 = QtWidgets.QListWidget(self.tab_3)
        self.listWidget_3.setGeometry(QtCore.QRect(100, 120, 615, 500))
        self.listWidget_3.setObjectName("listWidget_3")
        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QtWidgets.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.label_7 = QtWidgets.QLabel(self.tab_4)
        self.label_7.setGeometry(QtCore.QRect(15, 60, 70, 40))
        self.label_7.setObjectName("label_7")
        self.lineEdit_4 = QtWidgets.QLineEdit(self.tab_4)
        self.lineEdit_4.setGeometry(QtCore.QRect(100,70, 450, 41))
        self.lineEdit_4.setObjectName("lineEdit_4")
        self.pushButton_4 = QtWidgets.QPushButton(self.tab_4)
        self.pushButton_4.setGeometry(QtCore.QRect(450,70, 100, 41))
        self.pushButton_4.setObjectName("pushButton_4")
        self.label_8 = QtWidgets.QLabel(self.tab_4)
        self.label_8.setGeometry(QtCore.QRect(15, 125, 70, 40))
        self.label_8.setObjectName("label_8")
        self.listWidget_4 = QtWidgets.QListWidget(self.tab_4)
        self.listWidget_4.setGeometry(QtCore.QRect(100, 120, 615, 500))
        self.listWidget_4.setObjectName("listWidget_4")
        self.tabWidget.addTab(self.tab_4, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 409, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.label_9 = QtWidgets.QLabel(self.centralwidget)
        self.label_9.setGeometry(QtCore.QRect(550,-70, 300, 400))
        self.label_9.setObjectName("label_9")
        pix = QPixmap('logo.png')
        self.label_9.setPixmap(pix)
        #响应回车事件
        self.lineEdit.returnPressed.connect(partial(convert1,ui,wf_table))
        self.lineEdit_2.returnPressed.connect(partial(convert2,ui,hanlist,idf))
        self.lineEdit_3.returnPressed.connect(partial(convert3,ui,hanlist,norm_docs))
        self.lineEdit_4.returnPressed.connect(partial(convert4,ui,hanlist,norm_docs))

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(3)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton.setText(_translate("MainWindow", "搜索"))
        self.label.setText(_translate("MainWindow", "搜索内容"))
        self.label_2.setText(_translate("MainWindow", "搜索结果"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "布尔模型"))
        self.label_3.setText(_translate("MainWindow", "搜索内容"))
        self.pushButton_2.setText(_translate("MainWindow", "搜索"))
        self.label_4.setText(_translate("MainWindow", "搜索结果"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "向量模型"))
        self.label_5.setText(_translate("MainWindow", "搜索内容"))
        self.pushButton_3.setText(_translate("MainWindow", "搜索"))
        self.label_6.setText(_translate("MainWindow", "搜索结果"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("MainWindow", "概率模型"))
        self.label_7.setText(_translate("MainWindow", "搜索内容"))
        self.pushButton_4.setText(_translate("MainWindow", "搜索"))
        self.label_8.setText(_translate("MainWindow", "搜索结果"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), _translate("MainWindow", "语言模型"))

#显示函数
flag=[False]
def convert1(ui,table):
        ui.listWidget.clear()
        input = ui.lineEdit.text()
        start=time.time()
        flag=False
        for value in input:
            if value=="&" or value=="|" or value=="-" or value=="(" or value==")" or "A" in value or "O" in value:
                flag=True
        if flag:
            posting=boolSentence(input,table)
        else:
            posting=oriSentence(input,table)
        stop=time.time()
        if len(posting)==0:
            ui.listWidget.addItem("未检索到相应结果")
            return
        ui.listWidget.addItem("共花费"+str(stop-start)+"秒,结果如下:")
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
def convert2(ui,hanlist,idf):
    ui.listWidget_2.clear()
    input = ui.lineEdit_2.text()
    start=time.time()
    vq=to_vector(input,hanlist,idf)
    #dposting=distances(d,vq)
    if flag[0]==False:
        ui.listWidget_2.addItem("采用平方归一化方法")
        dposting=simplified_distances(norm_docs, vq)
        flag[0]=True
    else:
        ui.listWidget_2.addItem("采用最大值归一化方法")
        dposting=simplified_distances(max_docs, vq)
        flag[0]=False
    doc_sum=0
    for i in range(len(dposting)):
        if(dposting[i][1]!=0):
            doc_sum=doc_sum+1
        else:
            break
    doc_sum=min(20,doc_sum)
    stop=time.time()
    if doc_sum==0:
        ui.listWidget_2.addItem("未检索到相应结果")
        return
    else:
        ui.listWidget_2.addItem("共花费"+str(stop-start)+"秒,结果如下:")
        for i in range(doc_sum):
            no=dposting[i][0]
            f=open('songci\Doc'+str(no)+'.txt','r')
            txt=f.read()
            result="Doc"+str(no)+"\n"+"score:"+str(dposting[i][1])+"\n"
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
            ui.listWidget_2.addItem(result)
def convert3(ui,hanlist,docs):
    ui.listWidget_3.clear()
    input = ui.lineEdit_3.text()
    start=time.time()
    qv=to_01vector(input,hanlist)
    dposting=RSV_ranking(docs, qv, c)
    doc_sum=0
    for i in range(len(dposting)):
        if(dposting[i][1]!=0):
            doc_sum=doc_sum+1
        else:
            break
    doc_sum=min(20,doc_sum)
    stop=time.time()
    if doc_sum==0:
        ui.listWidget_3.addItem("未检索到相应结果")
        return
    else:
        ui.listWidget_3.addItem("共花费"+str(stop-start)+"秒,结果如下:")
        for i in range(doc_sum):
            no=dposting[i][0]
            f=open('songci\Doc'+str(no)+'.txt','r')
            txt=f.read()
            result="Doc"+str(no)+"\n"+"score:"+str(dposting[i][1])+"\n"
            timer=0
            for cc in txt:
                timer=timer+1
                if timer==37:
                    result=result+"\n"
                    timer=0
                if cc in input and cc!=" ":
                    result=result+"["+cc+"]"
                else:
                    result=result+cc
            ui.listWidget_3.addItem(result)
    #迭代优化
    Rlist=[]
    RN=10
    for i in range(RN):
        Rlist.append(dposting[i][0])
    for i in range(len(qv)):
        if qv[i]!=0:
            s=0
            for j in range(len(Rlist)):
                if docs[Rlist[j]-1][i]!=0:
                    s=s+1
            pi=s/RN
            if pi==0:
                pi=pi+0.000000001
            if pi==1:
                pi=pi-0.000000001
            ri=(df[i]-s+0.0000000001)/(270-RN)
            r[i]=ri
            p[i]=pi
            c[i]=math.log10(p[i]*(1-r[i])/((1-p[i])*r[i]))
def convert4(ui,hanlist,docs):
    ui.listWidget_4.clear()
    input = ui.lineEdit_4.text()
    start=time.time()
    vq=to_01vector(input,hanlist)
    lamb=0.7
    dposting=MLE_ranking(docs,vq, lamb, dfN)
    doc_sum=0
    for i in range(len(dposting)):
        if(dposting[i][1]!=0):
            doc_sum=doc_sum+1
        else:
            break
    doc_sum=min(20,doc_sum)
    stop=time.time()
    if doc_sum==0:
        ui.listWidget_4.addItem("未检索到相应结果")
        return
    else:
        ui.listWidget_4.addItem("共花费"+str(stop-start)+"秒,结果如下:")
        for i in range(doc_sum):
            no=dposting[i][0]
            f=open('songci\Doc'+str(no)+'.txt','r')
            txt=f.read()
            result="Doc"+str(no)+"\n"+"score:"+str(dposting[i][1])+"\n"
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
            ui.listWidget_4.addItem(result)
    





#界面启动
app = QtWidgets.QApplication(sys.argv)  
MainWindow = QtWidgets.QMainWindow()   
ui = Ui_MainWindow()                         
ui.setupUi(MainWindow)                 
MainWindow.show()                    
ui.pushButton.clicked.connect(partial(convert1,ui,wf_table))
ui.pushButton_2.clicked.connect(partial(convert2,ui,hanlist,idf))  
ui.pushButton_3.clicked.connect(partial(convert3,ui,hanlist,norm_docs))  
ui.pushButton_4.clicked.connect(partial(convert4,ui,hanlist,norm_docs))
sys.exit(app.exec_())            







    