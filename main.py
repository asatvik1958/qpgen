import mysql.connector
import random
import csv
from time import time as current_time
con=mysql.connector.connect(host='localhost', user='root', password='root')
cur=con.cursor()
if con.is_connected():
    print("Connection Successfull")
def check_database():
    cur.execute("SHOW DATABASES")
    l=cur.fetchall()
    if ('qpgen',) in l:
        return True
    return False

def create_database():
    db_found=check_database()
    if not db_found:
        cur.execute('CREATE DATABASE qpgen')
        con.commit()
        return False
    return True

def check_table():
    cur.execute('SHOW TABLES')
    l=cur.fetchall()
    if ('qpbank',) in l:
        return True
    return False

def create_table():
    tb_found=check_table()
    if not tb_found:
        cur.execute("CREATE TABLE qpbank (id int NOT NULL AUTO_INCREMENT, Subject varchar(50), Marks int, Question varchar(500),Primary Key(id))")
    return True

def connect_to_db():
    if not check_database():
        return False
    cur.execute("USE qpgen")
    return True

def is_empty_table():
    cur.execute("select count(*) from qpbank")
    l=cur.fetchall()
    if l[0][0]==0:
        return True
    return False
def choose_subject():
    print("Select subject from the following subjects: ")
    query="select distinct subject from qpbank"
    cur.execute(query)
    sub_list=cur.fetchall()
    for i in sub_list:
        print(i[0])
    while True:
        sub_ch=input("Enter your choice: ").upper()
        if (sub_ch,) not in sub_list:
            print("Subject not found... Try again")
        else:
            break
    return sub_ch

def choose_marks(sub_ch):
    query="select sum(marks) from qpbank where subject='{}'".format(sub_ch)
    cur.execute(query)
    max_marks=cur.fetchall()
    max_marks=int(max_marks[0][0])
    while True:
        marks_ch=int(input("Total marks for exam: (Max marks Available: {}): ".format(max_marks)))
        if marks_ch>max_marks:
            print("Entered marks is greater than available marks... Try again")
        elif marks_ch<=0:
            print("Total marks cant be zero or negative... Try again")
        else:
            break
    return marks_ch

def marks_distribution(sub_ch, marks_ch):
    md_ch={}
    query="select marks, count(marks) from qpbank where subject='{}' group by marks".format(sub_ch,marks_ch)
    cur.execute(query)
    md_data=cur.fetchall()
    md_list={}
    print("The available weightages and number of marks")
    print("Weightage\tNo. of Available questions")
    for i in md_data:
        print(i[0],(" "*20+"\t"),i[1])
        md_list[i[0]]=i[1]
    while True:
        weightage_ch=int(input("Enter weightage of a question: "))
        if weightage_ch not in md_list:
            print("Enter available weightage... Try again")
            continue
        
        noq_ch=int(input("Entern number of questions: "))
        if noq_ch<1:
            print("Number of questions cant be zero or negative... Try again")
            continue
        elif noq_ch>md_list[weightage_ch]:
            print("No. of questions cant be greater than available no. of questions")
            continue
        else:
            if weightage_ch in md_ch:
                print("Weightage already entered.. Try another")
                continue
            else:
                md_ch[weightage_ch]=noq_ch
        ch=input("Do you want to add more (Any key:Yes N:No): ").lower()
        if ch=='n':
            break
    return md_ch

def check_total(sub_ch):
    marks_ch=choose_marks(sub_ch)
    while True:
        md_ch=marks_distribution(sub_ch, marks_ch)
        sum=0
        for i in md_ch:
            sum=sum+(i*md_ch[i])
        if sum!=marks_ch:
            print("The total marks you entered: {}\nThe total marks acc. to marks distribution: {}".format(marks_ch, sum))
            marks_ch=choose_marks(sub_ch)
            continue
        else:
            break
    return (md_ch,marks_ch)

def select_random_q(rql,k):
    out_list=[]
    while len(out_list)!=k:
        rndm=random.randint(0,len(rql)-1)
        out_list.append(rql[rndm])
        rql.pop(rndm)
    return out_list

def create_qp(sub_ch,md_ch):
    question_list=[]
    for i in md_ch:
        rql=[]
        query="select id from qpbank where subject='{}' and marks = {}".format(sub_ch,i)
        cur.execute(query)
        q=cur.fetchall()
        for j in q:
            rql.append(j[0])
        question_list.append(select_random_q(rql,md_ch[i]))
    return question_list
    
       
def design_qp():
    if is_empty_table():
        print("Database Table is empty... Update data using Data Handler Wizard")
        return False
    exam_name_ch=input("Enter name of the exam: ")
    duration_ch=input("Enter duration of exam: ")
    sub_ch=choose_subject()
    md_ch,marks_ch=check_total(sub_ch)
    print("\nFinal Preview: \n")
    print("Exam Name: {}".format(exam_name_ch))
    print("Duration: {}".format(duration_ch))
    print("Subject: {}".format(sub_ch))
    print("Total Marks: {}".format(marks_ch))
    k=65
    for i in md_ch.keys():
        print("Section {}: {} question(s) each of {} mark(s)".format(chr(k),md_ch[i],i))
        k+=1
    print("Creating Question Paper")
    question_list=create_qp(sub_ch,md_ch)

    filename='./exports/qp-'+str(current_time())+'.txt'
    file=open(filename,'w')
    file.write("Exam Name: {}\n".format(exam_name_ch))
    file.write("Duration: {}\n".format(duration_ch))
    file.write("Subject: {}\n".format(sub_ch))
    file.write("Total Marks: {}\n\n".format(marks_ch))
    qno=1
    for i in question_list:
        for j in i:
            query="select question, marks from qpbank where id={}".format(j)
            cur.execute(query)
            qml=cur.fetchall()
            file.write(str(qno)+") "+ qml[0][0]+ " ({} Mark(s))".format(qml[0][1])+"\n\n")
            qno+=1
    print("Exported successfully to:",filename,"\n")
    file.close()
    return True

def update_db(f):
    if not check_table():
        print("create table first..")
        return False
    f.seek(0)
    csvr=csv.reader(f)
    next(csvr)
    csvlist=[]
    for i in csvr:
        csvlist.append(i)
    cur=con.cursor()
    cur.execute('select * from qpbank')
    data=cur.fetchall()
    dblist=[]
    tmp=[]
    for i in data:
        tmp=[i[1], str(i[2]), i[3]]
        dblist.append(tmp)

    
    for l in csvlist:
        if l not in dblist:
            cur.execute('insert into qpbank (Subject, Marks, Question) values("{}", {}, "{}")'.format(l[0],int(l[1]),l[2]))
            con.commit()
    print("Database Updated\n")
    return True

def export_to_csv():
    if not check_table():
        print("create table first..")
        return False
    ch=input("Do you want to export current data to csv (Y/N): ")
    if ch=='N':
        print("Operation terminated\n")
        return None
    filename='./exports/export-'+str(current_time())+'.csv'
    file=open(filename,'w', newline='')
    csvw=csv.writer(file)
    cur=con.cursor()
    cur.execute('select * from qpbank')
    data=cur.fetchall()
    dblist=[]
    tmp=[]
    for i in data:
        tmp=[i[1], str(i[2]),i[3]]
        dblist.append(tmp)
    csvw.writerows(dblist)
    print("Exported successfully to:",filename,"\n")
    file.close()
    return True
def data_handler_driver():
    try:
        f=open("data.csv")
        while True:
            print('''
DATA HANDLER WIZARD
Select your choice from the following options
    1.Upate data from data.csv ("exisiting records wont be added again")
    2.Export database data to csv
    3.Return to qpgen interface
    ''')
            ch=int(input("Enter your choice (1/2/3)"))
            if ch==1:
                update_db(f)
            elif ch==2:
                export_to_csv()
            elif ch==3:
                break
            else:
                print("Invalid choice")
        f.close()
    except Exception as e:
        print('The following error has occured:\n', repr(e))
        
def driver():
    if not connect_to_db():
        print("**************")
        print("Database Doesn't exist... New database created")
        create_database()
        connect_to_db()
        print("Table doesn't exist... New table created")
        create_table()
        print("**************")
    while True:
        print('''QP GEN - Interactive Interface
    Select your choice
    1. Create Question Paper
    2. Handle Database
    3. Exit
    ''')
        ch=int(input("Enter your choice(1/2/3):"))
        if ch==1:
            if check_table():
                design_qp()
            else:
                print("Table doesnt exist.. Create table using Data Handler Wizard")
        elif ch==2:
            data_handler_driver()
        elif ch==3:
            break
        else:
            print("Invalid choice")

driver()
cur.close()
con.close()
