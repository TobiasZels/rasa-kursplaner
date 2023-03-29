from bs4 import BeautifulSoup
from pymongo import MongoClient


#url = "https://spur.uni-regensburg.de/qisserver/pages/cm/exa/coursecatalog/showCourseCatalog.xhtml?_flowId=showCourseCatalog-flow&_flowExecutionKey=e1s1"

#r = requests.get(url)
#with open('file.txt', 'w') as file:
#    file.write(r.text)


#exit()
# HTML file path of the Course overiew page
data = open("Medieninfo.html","r").read()  
soup = BeautifulSoup(data, 'html.parser')

output = soup.find_all("tr", class_="treeTableCellLevel7")
output2 = soup.find_all("tr", class_="treeTableCellLevel8")
output4 = soup.find_all("tr", class_="treeTableCellLevel6")

text1 = []
text2 = []
text3 = []
text4 = []


for i in output:
    text1.append(i.text.strip())

for i in output2:
    text2.append(i.text.strip())

for i in output4:
    text3.append(i.text.strip())


course_object = []

for elements in text3:
    _id = elements.split(" ", 1)[0].replace('\n', '')
    _module = elements.split(" ", 2)[1]
    _lp = elements.split(" ", 2)[2].split("-", 1)[0]
    _type = elements.split(" ", 2)[2].split("-", 1)[1].split(" ", 2)[1]
    try:
        _name = elements.split(" ", 2)[2].split("-", 1)[1].split(" ", 2)[2]
    except:
        _name = ""
    _courses = []
    for course in text1:
        if _id in course.split(" ", 1)[0].replace('\n', ''):
            course_id = course.split("\n", 1)[0]
            course_name = course.split(" ", 1)[1].replace("- ", '')
            course_information = []
            for information in text2:
                if course_id in information.split("\n", 1)[0]:
                    group = information.split("\n", 4)[1].replace(' - ', '')
                    try:
                        time = information.split("\n", 4)[2].split(")", 1)[0]
                    except:
                        time = ""

                    

                    try:
                        dozent_replaced = information.split("\n", 4)[2].split(")", 1)[1].replace('Dozent/-in: ', "#")
                        room = dozent_replaced.split('#', 1)[0]
                        teacher = dozent_replaced.split('#', 1)[1].split('Bemerkung', 1)[0]
                        try:
                            additionalInfo = "Bemerkung:" + dozent_replaced.split('#', 1)[1].split('Bemerkung', 1)[1]
                        except:
                            additionalInfo = ""
                    except:
                        room = ""
                        teacher = ""
                        additionalInfo = ""
                    course_information.append({"group": group,
                                    "time": time,
                                    "room": room,
                                    "additionalInfo": additionalInfo,
                                    "teacher": teacher})


            _courses.append({"id": course_id,
                            "name": course_name,
                            "information": course_information})


    course_object.append({"id": _id,
                        "module": _module,
                        "lp": _lp.replace("(", "").replace(" LP) ", ""),
                        "type": _type,
                        "name": _name,
                        "subject": "Medieninformatik",
                        "graduation": "Bachelor",
                        "courses": _courses})

text3_split = text3[0].split(" ", 2)

client = MongoClient('localhost', 27017)
courseDatabase = client['kursplaner_database']


courseCollection = courseDatabase["courseCollection"]
studyCollection = courseDatabase["studyCollection"]



### SHOW
_course_information = []



_course_information.append({"group": group,
                "time": time,
                "room": room,
                "additionalInfo": additionalInfo,
                "teacher": teacher})


_courses.append({"id": course_id,
                "name": course_name,
                "information": _course_information})





# Kursobject, welches in einem Array gespeichert und später in der Datenbank abgespeichert wird
course_object.append({"id": _id,
                    "module": _module,
                    "lp": _lp.replace("(", "").replace(" LP) ", ""),
                    "type": _type,
                    "name": _name,
                    "subject": "Medieninformatik",
                    "graduation": "Bachelor",
                    "courses": _courses})




###
# Object mit dem Fach Medieninformatik
medieninformatik = {
"main_subject": 'Medieninformatik', 
"graduation": ['Bachelor', 'Master'], 
"bachelor_sub_subjects": ['Informationswissenschaft'], 
"master_sub_subjects": [], 
"min_semester": 6,
"max_semester": 9 
} 

client = MongoClient('localhost', 27017)

# Löschen der Datenbank zur vermeidung von duplikaten
client.drop_database('kursplaner_database')
courseDatabase = client['kursplaner_database']

# Erstellen der beiden Tables für Kurse und Fächer
courseCollection = courseDatabase["courseCollection"]
studyCollection = courseDatabase["studyCollection"]

# Eintragen der Daten in der Datenbank
rec = studyCollection.insert_one(medieninformatik)
rec = courseCollection.insert_many(course_object)

