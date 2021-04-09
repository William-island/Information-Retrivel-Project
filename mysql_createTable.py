import pymysql

#连接数据库
conn=pymysql.connect(host = "localhost",user = "root",passwd = "lb15951144240",db = "for_practice")
#创建游标
cur=conn.cursor()
#创建boolmatrix表
cur.execute('drop table if exists boolmatrix')
table_sql="""CREATE TABLE IF NOT EXISTS `boolmatrix` (
	  `id` int(11) NOT NULL AUTO_INCREMENT,
      `han` varchar(5) NOT NULL,
	  PRIMARY KEY (`id`)
	) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=1"""
cur.execute(table_sql)
column_sql="ALTER TABLE boolmatrix ADD COLUMN Doc%s int(11) NOT NULL;"
cur.executemany(column_sql,range(1,271))

#创建countmatrix表
cur.execute('drop table if exists countmatrix')
table_sql="""CREATE TABLE IF NOT EXISTS `countmatrix` (
	  `id` int(11) NOT NULL AUTO_INCREMENT,
      `han` varchar(5) NOT NULL,
	  PRIMARY KEY (`id`)
	) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=1"""
cur.execute(table_sql)
column_sql="ALTER TABLE countmatrix ADD COLUMN Doc%s int(11) NOT NULL;"
cur.executemany(column_sql,range(1,271))

#创建tfidf表
cur.execute('drop table if exists tfidf')
table_sql="""CREATE TABLE IF NOT EXISTS `tfidf` (
	  `id` int(11) NOT NULL AUTO_INCREMENT,
      `han` varchar(5) NOT NULL,
	  PRIMARY KEY (`id`)
	) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=1"""
cur.execute(table_sql)
column_sql="ALTER TABLE tfidf ADD COLUMN Doc%s real NOT NULL;"
cur.executemany(column_sql,range(1,271))

#创建wfidf表
cur.execute('drop table if exists wfidf')
table_sql="""CREATE TABLE IF NOT EXISTS `wfidf` (
	  `id` int(11) NOT NULL AUTO_INCREMENT,
      `han` varchar(5) NOT NULL,
	  PRIMARY KEY (`id`)
	) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=1"""
cur.execute(table_sql)
column_sql="ALTER TABLE wfidf ADD COLUMN Doc%s real NOT NULL;"
cur.executemany(column_sql,range(1,271))

cur.close()#先关闭游标
conn.close()#再关闭数据库连接
print('创建数据表成功')