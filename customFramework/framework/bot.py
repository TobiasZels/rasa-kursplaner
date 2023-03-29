import subprocess
import threading
import time
from pymongo import MongoClient
import eel
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.pagesizes import letter
import csv as csv
from framework import Bot, Dialogue, subDialogue 

########################
# Code outside of Framework
####################
# User Object
class User:
    # Courses not fully implementet in this Version
    finishedCourses = []
    possibleCourses = []
    selectedCourses = []
    finishedModules = []
    possibleModules = []
    selectedModules = []
    selectedSWS = 0
    semester = 0
    lp = 0
    restlp = 0

    def calculateRestLP(self):
        self.lp = 0
        for module in self.selectedModules:
            moduleData = courseCollection.find_one({"module": module})
            if not moduleData == None:
                self.lp += moduleData["lp"]

        self.restlp = 150 - self.lp

    def recalculateSWS(self, addition=False, module=None):
        if addition:
            moduleData = courseCollection.find_one({"module": module})
            self.selectedSWS += int(moduleData["lp"])
            return
        
        if self.selectedSWS > 0:
            moduleData = courseCollection.find_one({"module": self.selectedModules[-1]})

            self.selectedSWS -= int(moduleData["lp"])


currentUser = User()    
myBot = Bot()

# Database
client = MongoClient('localhost', 27017)
courseDatabase = client['kursplaner_database']
courseCollection = courseDatabase["courseCollection"]
studyCollection = courseDatabase["studyCollection"]

exempStudyplan = {
    1: ["PI-BA-M01.1", "PI-BA-M01.2", "MEI-BA-M01a.1", "MEI-BA-M01a.2", "MEI-BA-M02.1", "MEI-BA-M02.2"],
    2: ["PI-BA-M02.1", "PI-BA-M02.2", "MEI-BA-M01a.3", "MEI-BA-M03.1", "MEI-BA-M03.2", "MEI-BA-M04.1", "MEI-BA-M04.2"],
    3: ["PI-BA-M04.1", "PI-BA-M04.2", "MEI-BA-M06.1", "MEI-BA-M06.2"],
    4: ["PI-BA-M03.1", "PI-BA-M03.2", "MEI-BA-M07.1", "MEI-BA-M07.2", "MEI-BA-M08.1", "MEI-BA-M08.2"],
    5: ["MEI-BA-M05.1", "MEI-BA-M05.2", "MEI-BA-M09.1", "MEI-BA-M09.2", "MEI-BA-M10.1", "MEI-BA-M10.2", "MEI-BA-M10.3"],
    6: ["MEI-BA-M10.4"]}

def create_Schedule(tableDict):
    doc = SimpleDocTemplate("Zeitplan/simple_table.pdf", pagesize=letter)
    flowables = []
    data = [
            ["Uhrzeit", "Montag"],
            ["8 - 10", tableDict.get('mo8', "")],
            ["10 - 12", tableDict.get('mo10', "")],
            ["12 - 14", tableDict.get('mo12', "")],
            ["14 - 16", tableDict.get('mo14', "")],
            ["16 - 18", tableDict.get('mo16', "")],
            ["18 - 20", tableDict.get('mo18', "")],
            ["Uhrzeit", "Dienstag"],
            ["8 - 10",  tableDict.get('di8', "")],
            ["10 - 12", tableDict.get('di10', "")],
            ["12 - 14", tableDict.get('di12', "")],
            ["14 - 16", tableDict.get('di14', "")],
            ["16 - 18", tableDict.get('di16', "")],
            ["18 - 20", tableDict.get('di18', "")],
            ["Uhrzeit", "Mittwoch"],
            ["8 - 10",  tableDict.get('mi8', "")],
            ["10 - 12", tableDict.get('mi10', "")],
            ["12 - 14", tableDict.get('mi12', "")],
            ["14 - 16", tableDict.get('mi14', "")],
            ["16 - 18", tableDict.get('mi16', "")],
            ["18 - 20", tableDict.get('mi18', "")],
            ["Uhrzeit", "Donnerstag"],
            ["8 - 10",  tableDict.get('do8', "")],
            ["10 - 12", tableDict.get('do10', "")],
            ["12 - 14", tableDict.get('do12', "")],
            ["14 - 16", tableDict.get('do14', "")],
            ["16 - 18", tableDict.get('do16', "")],
            ["18 - 20", tableDict.get('do18', "")],
            ["Uhrzeit", "Freitag"],
            ["8 - 10",  tableDict.get('fr8', "")],
            ["10 - 12", tableDict.get('fr10', "")],
            ["12 - 14", tableDict.get('fr12', "")],
            ["14 - 16", tableDict.get('fr14', "")],
            ["16 - 18", tableDict.get('fr16', "")],
            ["18 - 20", tableDict.get('fr18', "")],
            ]
    tbl = Table(data)
    flowables.append(tbl)
    doc.build(flowables)




# functions
def get_main_subject():
    m_subject = myBot.slotHashmap["subjects"][0]
    if "semester" in myBot.slotHashmap:
        myBot.deleteSlotValue('semester')
    
    if not studyCollection.find_one({"main_subject": m_subject}) == None:
        myBot.setSlotValue("main_subject", m_subject)
        get_graduation() #enables user to enter more information in one dialogue 
        return

    # Not a valid subject
    myBot.outputText("Das gewählte Studienfach ist nicht verfügbar.")
    myBot.jumpToDialog(utter_ask_main_subject)

def get_graduation():
    m_graduation = None
    if "graduation" in myBot.slotHashmap:
        m_graduation = myBot.slotHashmap["graduation"][0]

    # load the object form the Database
    main_subject_data = studyCollection.find_one({"main_subject": myBot.slotHashmap["main_subject"]})

    for grad in main_subject_data['graduation']:
        if m_graduation == grad:
            myBot.jumpToDialog(utter_ask_sub_subject)
            myBot.setSlotValue("graduation", m_graduation)
            get_sub_subject()
            return

    # check if we should throw an error
    if utter_ask_graduation.getBotInstance().getIndex() > utter_ask_graduation.getIndex():
        myBot.outputText("Der gewählte Abschluss ist für das geswünschte Studienfach nicht verfügbar.")
        myBot.jumpToDialog(utter_ask_graduation)
        return

def get_sub_subject():
    m_subject = None

    if "subjects" in myBot.slotHashmap:
        m_subject = myBot.slotHashmap["subjects"][-1]

    sub_subject_list = []
    # load the object form the Database
    main_subject_data = studyCollection.find_one({"main_subject": myBot.slotHashmap["main_subject"]})
    if myBot.slotHashmap["graduation"] == "Bachelor":
        # test if array is empty
        if len(main_subject_data["bachelor_sub_subjects"]) == 0:
            myBot.jumpToDialog(utter_ask_semester)
            validate_semester_select()
            return

        for sub in main_subject_data["bachelor_sub_subjects"]:
            if m_subject == sub:
                myBot.jumpToDialog(utter_ask_semester)
                myBot.setSlotValue("sub_subject", m_subject)
                validate_semester_select()
                return
    else:
        # test if array is empty
        if len(main_subject_data["master_sub_subjects"]) == 0:
            myBot.jumpToDialog(utter_ask_semester)
            validate_semester_select()
            return

        for sub in main_subject_data["master_sub_subjects"]:
            if m_subject == sub:
                myBot.jumpToDialog(utter_ask_semester)
                myBot.setSlotValue("sub_subject", m_subject)
                validate_semester_select()
                return

    if utter_ask_sub_subject.getBotInstance().getIndex() > utter_ask_sub_subject.getIndex():
        myBot.outputText("Das gewählte Nebenfach ist nicht mit dem Hauptfach kombinierbar.")
        myBot.slotHashmap["subjects"].pop(-1)
        myBot.jumpToDialog(utter_ask_sub_subject)
        return

def validate_semester_select():
    m_semester = None
    if "semester" in myBot.slotHashmap:
        m_semester = myBot.slotHashmap["semester"][0]
    else:
        return
        
    
    main_subject_data = studyCollection.find_one({"main_subject": myBot.slotHashmap["main_subject"]})

    if int(m_semester) <= int(main_subject_data["max_semester"]):
        myBot.jumpToDialog(utter_validate_study_data)
        myBot.setSlotValue("semester", m_semester)
        myBot.setSlotValue("min_semester", main_subject_data["min_semester"])
        myBot.setSlotValue("max_semester", main_subject_data["max_semester"])
        return
    
    if int(m_semester) > int(main_subject_data["max_semester"]):
        myBot.outputText("Bitte geben sie eine Semesteranzahl zwischen " + str(1) + " und " + str(main_subject_data["max_semester"]) + " ein.")
        myBot.jumpToDialog(utter_ask_semester)
        return

def jump_to_selection(dia, offset = -1):
    myBot.jumpToDialog(dia, offset=offset)

def validate_max_semester_select():
    m_semester = None
    if "semester" in myBot.slotHashmap:
        m_semester = myBot.slotHashmap["semester"][-1]

    main_subject_data = studyCollection.find_one({"main_subject": myBot.slotHashmap["main_subject"]})

    if int(main_subject_data["min_semester"]) <= int(m_semester) <= int(main_subject_data["max_semester"]):
        myBot.setSlotValue("study_duration", m_semester)
        myBot.setSlotValue("sws_empf", 15)
        return
    
    myBot.outputText("Bitte geben sie eine Semesteranzahl zwischen " + str(main_subject_data["min_semester"]) + " und " + str(main_subject_data["max_semester"]) + " ein.")
    myBot.jumpToDialog(utter_ask_study_time)

def validate_selected_Modules():
    selectedModules = myBot.slotHashmap["module"]
    for modules in selectedModules:
        currentUser.finishedModules.append(modules)

def validate_selected_Courses():
    selectedCourses = myBot.slotHashmap["courses"]
    for course in selectedCourses:
        currentUser.finishedCourses.append(course)
    
def validate_sws():
    sws = myBot.slotHashmap["semester"]
    currentUser.selectedSWS = int(sws[-1])
    currentUser.calculateRestLP()

def seach_course_list():
    if len(currentUser.possibleModules) == 0:
        courseData = courseCollection.find({"subject": myBot.slotHashmap["main_subject"]})
        lastSemCourses = []
        currentSemCourses = []
        futureSemCourses = []
        for courses in courseData:
            if not courses["module"] in currentUser.finishedModules:
                if len(courses["courses"]) > 0:
                    if courses["type"] == "V" or courses["type"] == "S" or courses["type"] == "Ü":
                        for i in range(6):
                            thisSem = i +1
                            if courses["module"] in exempStudyplan[thisSem]:
                                if thisSem < currentUser.semester:
                                    lastSemCourses.append(courses["module"])
                                if thisSem > currentUser.semester:
                                    futureSemCourses.append(courses["module"])
                                if thisSem == currentUser.semester:
                                   currentSemCourses.append(courses["module"])
        # sorted by relevance 
        currentUser.possibleModules = lastSemCourses + currentSemCourses + futureSemCourses

    # if still empty no courses could be found ( shouldn't happen in this demo)
    if len(currentUser.possibleModules) == 0:
        myBot.outputText("Es konnten keine weiteren Kurse gefunden werde. Wollen sie ihre Suchkriterien ändern?")
        # jumpt to the selection dialogue
        # TODO jump_to_selection(user_aditional_courses_dialog_yes)
        return
    
    # finally remove the first entry from the array and save it into next course
    myBot.setSlotValue("next_module", currentUser.possibleModules[0])
    del currentUser.possibleModules[0]

    currentCourse = courseCollection.find_one({"module": myBot.slotHashmap["next_module"]})
    myBot.setSlotValue("next_course_list",  "")
    coursesArray = []
    for course in currentCourse["courses"]:
        coursesArray.append(course["name"])
        myBot.setSlotValue("next_course_list", coursesArray) 

def get_information():
    currentCourse = courseCollection.find_one({"module": myBot.slotHashmap["next_module"]})
    for course in currentCourse["courses"]:
        for information in course["information"]:
            myBot.outputText(str(information["group"]) + " finded am " + str(information["time"]) + " in Raum " + str(information["room"]) + " statt. Geleitet wird der Kurs von " + str(information["teacher"]) + ". " + str(information["additionalInfo"]) )
    myBot.jumpToDialog(utter_found_course, 0)

def select_course():
    if "next_course" in myBot.slotHashmap:
        currentUser.selectedCourses.append(myBot.slotHashmap["next_course"])
    currentUser.selectedModules.append(myBot.slotHashmap["next_module"])
    # TODO: get module

    # create schedule
    create_Schedule(coursesToDict())
    myBot.setSlotValue("schedule_link", "dem Ordner Zeitplan einsehen (optional eine Url erstellen)")


    currentUser.recalculateSWS()
    if currentUser.selectedSWS > 0:
        myBot.jumpToDialog(action_finish_data_collection, 0)
        return

def deny_course():
    myBot.jumpToDialog(action_finish_data_collection, 0)
    
def remove_course():
    # TODO: oposite of the function above
    if "module" in myBot.slotHashmap:
        if myBot.slotHashmap["module"][0] in currentUser.selectedModules:
            currentUser.selectedModules.remove(myBot.slotHashmap["module"][0])
            create_Schedule(coursesToDict())
            currentUser.recalculateSWS(addition=True, module=myBot.slotHashmap["module"][0])
        else:
            myBot.outputText("Der angegebne Kurs ist nicht in ihrer Kursliste!")
            myBot.jumpToDialog(utter_ask_for_changes_to_courseplan, 0)

    if currentUser.selectedSWS > 0:
        myBot.outputText("Es wird nach weiteren Kursen gesucht.")
        myBot.jumpToDialog(action_finish_data_collection, 0)
        return
    else:
        myBot.jumpToDialog(utter_ask_for_changes_to_courseplan, 0)

def check_low_lp():
    myBot.setSlotValue("lp_left", currentUser.restlp)
    if currentUser.restlp > 15:
        jump_to_selection(utter_ask_for_changes_to_courseplan) 
# Sub Dialoge
def coursesToDict():
    result = {}
    for courses in currentUser.selectedModules:
        module = courseCollection.find_one({"module": courses})
        currentCourse = module["courses"][0]
        timeKey = ""

        # An ugly solution
        if "Montag" in currentCourse["information"][0]["time"]:
            timeKey += "mo"
        if "Dienstag" in currentCourse["information"][0]["time"]:
            timeKey += "di"
        if "Mittwoch" in currentCourse["information"][0]["time"]:
            timeKey += "mi"
        if "Donnerstag" in currentCourse["information"][0]["time"]:
            timeKey += "do"
        if "Freitag" in currentCourse["information"][0]["time"]:
            timeKey += "fr"

        # Same for time slots
        if "bis 10:00" in currentCourse["information"][0]["time"]:
            timeKey += "8"
        if "bis 12:00" in currentCourse["information"][0]["time"]:
            timeKey += "10"
        if "bis 14:00" in currentCourse["information"][0]["time"]:
            timeKey += "12"
        if "bis 16:00" in currentCourse["information"][0]["time"]:
            timeKey += "14"
        if "bis 18:00" in currentCourse["information"][0]["time"]:
            timeKey += "16"
        if "bis 20:00" in currentCourse["information"][0]["time"]:
            timeKey += "18"

        result[timeKey] = str(courses) + ": " + str(currentCourse["name"]) 
            
    return result

# Main Dialoge

# Intro
intro = Dialogue(botResponse="Willkommen beim Kursplaner, im nachfolgenden werde ich sie bei der Auswahl ihrer Kurse für das nachfolgende Semester unterstützen.")

# Main Subject
utter_ask_main_subject = Dialogue(botResponse="Welches Fach studieren sie aktuell als Hauptfach?")
user_intent_main_subject = Dialogue(userIntent="select_fach", errorResponse="Bitte geben sie ein gültiges Studienfach ein.")
action_get_main_subject = Dialogue(action=lambda: get_main_subject())

# Graduation
utter_ask_graduation = Dialogue(botResponse="Welchen Abschluss verfolgen sie?")
user_intent_graduation= Dialogue(userIntent="select_graduation")
action_get_graduation = Dialogue(action=lambda: get_graduation())

# Sub Subject
utter_ask_sub_subject = Dialogue(botResponse="Was ist ihr Nebenfach?")
user_intent_sub_subject= Dialogue(userIntent="select_fach")
action_get_sub_subject = Dialogue(action=lambda: get_sub_subject())

# Semester
utter_ask_semester = Dialogue(botResponse="Für welches Semester möchten sie einen Stundenplan erstellen?")
user_intent_semester = Dialogue(userIntent="select_semester")
action_get_semester = Dialogue(action=lambda: validate_semester_select())

# validate data
jump_to_main_subject = Dialogue(action= lambda: jump_to_selection(utter_ask_main_subject, offset=0))

utter_validate_study_data = Dialogue(botResponse="Sie befinden sich zurzeit im {{semester}} Semester des {{graduation}} in {{main_subject}} mit {{sub_subject}}, ist das richtig?")
user_validate_dialog_yes = Dialogue(userIntent="confirm", index=utter_validate_study_data)
user_validate_dialog_no = Dialogue(userIntent="reject", index=utter_validate_study_data, subNodes=[jump_to_main_subject])

# Select max study time
utter_ask_study_time = Dialogue(botResponse="Bis zu welchem Semester wollen Sie ihr Studium abschließen, empfohlen wird für {{main_subject}}  {{min_semester}} Semester mit einer maximalen Studiendauer von {{max_semester}} Semestern.")
user_intent_study_time = Dialogue(userIntent="select_semester")
action_get_study_time = Dialogue(action=lambda: validate_max_semester_select())

# Select finished Modules
action_get_modules = Dialogue(action=lambda: validate_selected_Modules())
utter_give_flex_now = Dialogue(botResponse="Ihre bereits abgeschlossenen Module können sie unter (Flex-Now Link) einsehen.")
jumpt_to_models = Dialogue(action=lambda: jump_to_selection(utter_ask_for_modules))

jumpt_to_courses= Dialogue(action=lambda: jump_to_selection(utter_ask_for_courses, 0))

utter_ask_for_modules = Dialogue(botResponse="Welche Module haben sie bisher Abgeschlossen?")
user_intent_modules = Dialogue(userIntent="select_module", index=utter_ask_for_modules, subNodes=[action_get_modules])
user_intent_ask_for_help = Dialogue(userIntent="needs_help", index=utter_ask_for_modules, subNodes=[utter_give_flex_now, jumpt_to_models])
user_intent_no_courses = Dialogue(userIntent="reject", index=utter_ask_for_modules, subNodes=[jumpt_to_courses])
# Select courses
action_get_courses = Dialogue(action=lambda: validate_selected_Courses())

utter_ask_for_courses = Dialogue(botResponse="Haben sie Kurse aus noch nicht abgeschlossenen Modulen bereits besucht, wenn ja welche?")
user_validate_courses_no = Dialogue(userIntent="reject", index=utter_ask_for_courses)
user_intent_select_course = Dialogue(userIntent="select_course", index=utter_ask_for_courses, subNodes=[action_get_courses])

# Select time frame 
utter_ask_for_sws = Dialogue(botResponse="Wie viel Zeit möchten sie für ihr Studium dieses Semester aufbringen, um das Studium in der gewünschten Zeit abzuschließen werden {{sws_empf}} SWS empfohlen.")
user_intent_sws = Dialogue(userIntent="select_sws")
action_get_sws= Dialogue(action=lambda: validate_sws())

# finish Datenerhebung


utter_finish_data_collection = Dialogue(botResponse="Bitte warten sie während ich für Sie nach Kursen suche...")
action_finish_data_collection = Dialogue(action=lambda: seach_course_list())

# Part one of the Bot getting the information from the user
Datenerhebung_Container = Dialogue(subNodes=[
    utter_ask_main_subject, user_intent_main_subject, action_get_main_subject,
    utter_ask_graduation, user_intent_graduation, action_get_graduation,
    utter_ask_sub_subject, user_intent_sub_subject, action_get_sub_subject,
    utter_ask_semester, user_intent_semester, action_get_semester,
    utter_validate_study_data, user_validate_dialog_yes, user_validate_dialog_no,
    utter_ask_study_time, user_intent_study_time, action_get_study_time,
    utter_ask_for_modules, user_intent_no_courses, user_intent_modules, user_intent_ask_for_help,
    utter_ask_for_courses, user_validate_courses_no, user_intent_select_course,
    utter_ask_for_sws, user_intent_sws, action_get_sws,
    utter_finish_data_collection
])

# Select course
action_wants_information = Dialogue(action= lambda: get_information())

"Kurs {next_course} wurde dem Stundenplan hinzugefügt."
"Der Kurs {next_course} konnte leider nicht gefunden werden."

action_selects_course = Dialogue(action= lambda: select_course())
action_deny_course = Dialogue(action= lambda: deny_course())


utter_found_course = Dialogue(botResponse="Für das Modul {{next_module}} werden die Kurse {{next_course_list}} angeboten. Wählen sie ob und welchen Kurs sie belegen wollen oder stellen sie Fragen zu den einzelnen Kursen für weitere Informationen.")
user_intent_ask_more_information = Dialogue(userIntent="wants_information", index=utter_found_course, subNodes=[action_wants_information])
user_intent_select_course = Dialogue(userIntent="accept_course", index=utter_found_course, subNodes=[action_selects_course])
user_intent_reject_course = Dialogue(userIntent="reject", index=utter_found_course, subNodes=[action_deny_course])


# check for low lp
action_check_for_low_lp = Dialogue(action= lambda: check_low_lp())
    # if not low lp
jump_to_found_course = Dialogue(action=lambda: jump_to_selection(utter_found_course))

utter_ask_for_aditional_courses = Dialogue(botResponse="Für den Abschluss ihres Studiums benötigen sie zusätzlich nur noch {{lp_left}}, möchten sie einen weiteren Kurs belegen um diese lp zu erreichen?")
user_aditional_courses_dialog_yes = Dialogue(userIntent="confirm", index=utter_ask_for_aditional_courses, subNodes=[jump_to_found_course])
user_aditional_courses_dialog_no = Dialogue(userIntent="reject", index=utter_ask_for_aditional_courses)

# finish studnenplan

## Subdialoge
action_add_course = Dialogue(action= lambda: select_course())
action_remove_course = Dialogue(action= lambda: remove_course())
action_jump_to_ask_change = Dialogue(action= lambda: jump_to_selection(utter_ask_what_changes, 0))
return_to_ask_changes = Dialogue(action= lambda: jump_to_selection(utter_ask_for_changes_to_courseplan, 0))

utter_remove_course = Dialogue(botResponse="Sind sie sicher das der Kurs {{module}} von ihrem Stundenplan entfernt werden soll?")
user_wants_removal = Dialogue(userIntent="confirm", index=utter_remove_course, subNodes=[action_remove_course])
user_reject_removal = Dialogue(userIntent="reject", index=utter_remove_course, subNodes=[action_jump_to_ask_change])

utter_ask_what_changes = Dialogue(botResponse="Geben sie an welcher Kurs aus ihrem Stundenplan gelöscht werden soll oder nennen sie einen Kurs um diesen hinzuzufügen.")
user_intent_add_course = Dialogue(userIntent="select_course", index=utter_ask_what_changes, subNodes=[action_add_course])
user_intent_delete_course = Dialogue(userIntent="remove_course", index=utter_ask_what_changes, subNodes=[utter_remove_course, user_wants_removal, user_reject_removal])
user_cancel = Dialogue(userIntent="cancel", index=utter_ask_what_changes, subNodes=[return_to_ask_changes])



## Main dialog
utter_ask_for_changes_to_courseplan = Dialogue(botResponse="Ihren Stundenplan können sie unter {{schedule_link}} einsehen. Möchten sie den Stundenplan übernehmen oder möchten sie Änderungen an diesem Vornehmen?")
user_reject_changes = Dialogue(userIntent="user_happy", index=utter_ask_for_changes_to_courseplan)
user_wants_changes = Dialogue(userIntent="user_unhappy", index=utter_ask_for_changes_to_courseplan, subNodes=[utter_ask_what_changes, user_intent_add_course, user_intent_delete_course, user_cancel])

# return stundenplan
utter_return_stundenplan = Dialogue(botResponse="Ihren fertigen Stundenplan können sie unter {{schedule_link}} einsehen.")


# Part two of the Bot selecting courses
Kursauswahl_Container = Dialogue(subNodes=[
    action_finish_data_collection,
    utter_found_course, user_intent_ask_more_information, user_intent_select_course, user_intent_reject_course,
    action_check_for_low_lp, utter_ask_for_aditional_courses, user_aditional_courses_dialog_no, user_aditional_courses_dialog_yes,
    utter_ask_for_changes_to_courseplan, user_reject_changes, user_wants_changes,
    utter_return_stundenplan
])


last_information = Dialogue(botResponse="")
bot_finished = Dialogue(botResponse="Ich hoffe ich konnte ihnen weiterhelfen, vergessen sie nicht ihre Kurse im Studienportal zu belegen.")

myBot.addDialogue([intro, Datenerhebung_Container, Kursauswahl_Container, last_information, bot_finished])

def run_Rasa():
    subprocess.call(["rasa", "run" ,"--enable-api", "-m", "rasa-model/nlu-20230329-221703-tough-leg.tar.gz"])


def startEel():
    eel.init('gui')
    eel.start('main.html')


def startMain():
    myBot.mainLoop(startfunction=lambda: time.sleep(30))

f = threading.Thread(target=startEel)
t = threading.Thread(target=run_Rasa)
s = threading.Thread(target=startMain)
t.start()
s.start()
f.start()


# The courseplanner app uses EEL for its frontend.

# EEL
@eel.expose
def returnChat(input):
    Bot.ainput = input

