import xlrd


# wbname==即文件名称，sheetname==工作表名称，可以为空，若为空默认第一个工作表
def readwb(wbname):
    dataset = []
    workbook = xlrd.open_workbook(wbname)
    table = workbook.sheets()[2]
    for row in range(table.nrows):
        try:
            if table.row_values(row)[1] > 1000:
                dataset.append(table.row_values(row)[0])
        except:
            continue
    return dataset


data = readwb("data/7-9月北京应答原始交互日志/8月-中国移动10086微信.xlsx")

o = open("standardQuestion.txt", "w")
for x in data:
    o.write(x.strip())
    o.write("\n")
    o.flush()
o.close()
