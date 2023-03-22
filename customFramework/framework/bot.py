import re
import subprocess
import os
import threading
import time
import requests
import json
from pymongo import MongoClient
import eel
import concurrent.futures

# For unknown reasons it won't work on Windows without this line
# Mac works
# Linux works
# But no windows doesn't accept that its not needed
# Even WSL has no problem without it
thread_pool_ref = concurrent.futures.ThreadPoolExecutor


class Dialogue:
    index = None
    userIntent = None
    action = None
    botResponse = None
    botInstance = None
    templateResponse = None
    hasSlots = False
    subNodes = []
    parent = None
    errorResponse = None

    def __init__(self, index=None, userIntent=None, action=None, botResponse=None, subNodes=None, errorResponse=None):
        self.index = index
        self.userIntent = userIntent
        self.action = action
        self.botResponse = botResponse
        self.subNodes = subNodes
        self.templateResponse = botResponse
        self.errorResponse = errorResponse
        if not botResponse == None:
            slotFields = re.findall("\{\{(.*?)\}\}", botResponse)
            if len(slotFields) > 0:
                self.hasSlots = True
        # Set Parents for subnodes
        if not subNodes == None:
            for node in subNodes:
                node.setParent(self)
            

    def getIndex(self):
        return self.index     
    
    def setIndex(self, index):
        self.index = index

    def getUserIntent(self):
        return self.userIntent

    def getBotResponse(self):
        return self.botResponse 

    def getHasSlots(self):
        return self.hasSlots
    
    def setBotInstance(self, instance):
        self.botInstance = instance

    def getBotInstance(self):
        return self.botInstance

    def getFunction(self):
        return self.action
    
    def getSubNodes(self):
        return self.subNodes
    
    def setParent(self, parent):
        self.parent = parent
    
    def getParent(self):
        return self.parent
    
    def getErrorResponse(self):
        return self.errorResponse
    
    def fillSlotIntoResponse(self, slots):
        slotFields = re.findall("\{\{(.*?)\}\}", self.botResponse)
        for slot in slotFields:
            if slot in slots:
                self.botResponse = self.botResponse.replace("{{" + slot + "}}", slots[slot])

    def resetResponse(self):
        self.botResponse = self.templateResponse


class subDialogue:
    intent = None
    dialogueList = None
    disabled = False

    def __init__(self, userIntent, dialogue, standardDisabled=False):
        self.intent = userIntent
        self.dialogueList = dialogue
        self.disabled = standardDisabled

    def getIntent(self):
        return self.intent
    
    def getDialogue(self):
        return self.dialogueList
    
    def getDisabled(self):
        return self.disabled
    
    def enable(self):
        self.disabled = False
    
    def disable(self):
        self.disable = True


class Bot:
    mainRoutine = 0
    subRoutine = 0
    highestIndex = 0
    NLUUrl = "http://localhost:5005/model/parse"
    exit = False
    # What i learned in Codinginterviews if you have no clue how to solve a task just throw a random
    # Hashmap at it ^_^
    dialogueHashmap = {}
    subRoutineList = []
    slotHashmap = {}
    ainput = None

    def __init__(self, slotHashmap={}, index = 0):
        self.mainRoutine = index
        self.dialogueHashmap = {}
        self.slotHashmap = slotHashmap
        self.exit = False
    
    def mainLoop(self, startfunction=None):
        if not startfunction == None:
            startfunction()
        while(not self.exit):
            # if the dialogue went outside the Hashmap end the loop/restart the loop
            if not self.mainRoutine in self.dialogueHashmap:
                #TODO do something here
                self.mainRoutine = 0
                self.exit = True
                continue

            dialogueList = self.dialogueHashmap[self.mainRoutine]
            needsInteraction = False

            # Checks if the turns needs userInput
            for dialogue in dialogueList:
                if not dialogue.getUserIntent() == None:
                    needsInteraction = True

                # Starts with running code if there is some function
                if not dialogue.getFunction() == None:
                    dialogue.getFunction()()


            # If Userinteraction is needed get the Input and process it to get slots/intets
            if needsInteraction:
                self.activateChat()
                intent, slots = self.fetchFromNLU(self.awaitInput())
                success = False
                for dialogue in dialogueList:
                    # if the intent could be found then yay set the slot and continue
                    if dialogue.getUserIntent() == intent:
                        for elements in slots:
                            self.slotHashmap[elements] = slots[elements]
                        self.mainRoutine += 1
                        if not dialogue.getSubNodes() == None:
                            subBot = Bot(slotHashmap=self.slotHashmap)
                            subBot.addDialogue(dialogue.getSubNodes())
                            subBot.mainLoop()
                        success = True
                        break
                    
                if success:
                    continue
                # if not the user entered something he wasn't supposed to so we first look into the subRoutine TODO

                for subDialogue in self.subRoutineList:
                    # First we need to confirm if the subDialogue is enabled at this point in time
                    if subDialogue.getDisabled() == False:
                        if subDialogue.getIntent() == intent:
                            subBot = Bot(slotHashmap=self.slotHashmap)
                            subBot.addDialogue(subDialogue.getDialogue())
                            subBot.addSubDialogue(dialogueList = self.subRoutineList)
                            subBot.mainLoop()
                            # then go back one step so the user sees the last question again
                            self.mainRoutine -= 1
                # if even in the sub routibe nothing could be found then we need to return an error TODO
                self.outputText("I didn't understand your message")
                continue

            # Print out the bot message and fill slots at runtime      
            for dialogue in dialogueList:
                if dialogue.getHasSlots() == True:
                    dialogue.fillSlotIntoResponse(self.slotHashmap)

                if not dialogue.getBotResponse() == None:   
                    self.outputText(dialogue.getBotResponse())
                # Reset response to empty the filled slots again
                dialogue.resetResponse()

                # To enable Containering of Nodes
                if not dialogue.getSubNodes() == None:
                    subBot = Bot(slotHashmap=self.slotHashmap)
                    subBot.addDialogue(dialogue.getSubNodes())
                    subBot.addSubDialogue(dialogueList = self.subRoutineList)
                    subBot.mainLoop()

            # mainRoutine should only increase on successfull interaktions
            self.mainRoutine += 1

    def addDialogue(self, dialogueArray):

        # for each dialogue we add it to the hashmap
        for dialogue in dialogueArray:
            # set bot instance
            dialogue.setBotInstance(self)
            # Check if the dialogue has a object attached and set it to an index
            if isinstance(dialogue.getIndex(), Dialogue):
                dialogue.setIndex(dialogue.getIndex().getIndex() + 1)

            # If the dialogue has an index append the dialogue to the index and set the highest index to it
            if not dialogue.getIndex() == None:
                if dialogue.getIndex() in self.dialogueHashmap:
                    self.dialogueHashmap[dialogue.getIndex()].append(dialogue)
                else:
                    self.dialogueHashmap[dialogue.getIndex()] = [dialogue]
                    self.highestIndex += 1
                
                continue
            # If index doesnt exist set the index to the highest value and add it to the hashmap
            dialogue.setIndex(self.highestIndex)
            self.dialogueHashmap[self.highestIndex] = [dialogue]
            self.highestIndex += 1

    def addSubDialogue(self, dialogueList):
        self.subRoutineList = dialogueList


    def setSlotValue(self, key,  value):
        self.slotHashmap[key] = value
    
    def setIndex(self, index):
        self.mainRoutine = index

    def hasExited(self):
        return self.exit
    
    def setExited(self, exited):
        self.exit = exited

    def jumpToDialog(self, dialog):
        # AArgh first we need to get the container and then iterate through painge, but every container should
        # run the loop anyways and jumping into the same container is not a problem cause of parents ( pain ) we
        # can ignore that problem if we break the loop we are in after iterating through
        dialog.getBotInstance().setIndex(dialog.getIndex())

        if dialog.getBotInstance().hasExited():
            dialog.getBotInstance().setExited(False)
            dialog.getBotInstance().mainLoop()
        
        # Iterate to the outmost Instance
        if not dialog.getParent() == None:
            dialog.getParent().getBotInstance().jumpToDialog(dialog.getParent())

        # Set the index

    def getIndex(self):
        return self.mainRoutine
    
    def outputText(self, text):
        eel.botMessage(text)


    def activateChat(self):
        eel.activateChat()

    def awaitInput(self):
        Bot.ainput = None

        while Bot.ainput == None:
            time.sleep(1)   
        return Bot.ainput


# Most important function for the Bot, for the course planner i used Rasa with a custom trained nlu model, but every NLU 
# Framework can be used. The function has an input issued by the user and has to return an intent that describes the user intent 
# and slots which has entity data in it. In future iterations the Rasa Framework can be replaced by more sufisticated solutions like
# Chat GPT. 
    def fetchFromNLU(self, input):

        object = {'text': input}
        slots = {}

        # Post request to the Rasa NLU model server
        response = requests.post(self.NLUUrl, json=object)
        responseObject = json.loads(response.text)
        # Grab the intent 
        intent = responseObject["intent"]["name"]
        # Grab all the Entities to fill the slots
        for entity in responseObject["entities"]:
            slot = entity["value"]
            slotname = entity["entity"]
            if slotname in slots:
                slots[slotname].append(slot)
                continue
            slots[slotname] = [slot]

        return (intent, slots)

########################
# Code outside of Framework
####################

myBot = Bot()
client = MongoClient('localhost', 27017)
courseDatabase = client['kursplaner_database']

courseCollection = courseDatabase["courseCollection"]

record = {
"main_subject": 'Medieninformatik', 
"graduation": ['Bachelor', 'Master'], 
"bachelor_sub_subjects": ['Informationswissenschaft'], 
"master_sub_subjects": [], 
"min_semester": 6,
"max-semester": 9 
} 
# rec = courseCollection.insert_one(record)

#for i in mydatabase.myTable.find({title: 'MongoDB and Python'})
#    print(i)

# functions
def get_main_subject():
    m_subject = myBot.slotHashmap["subjects"][0]
    
    if not courseCollection.find_one({"main_subject": m_subject}) == None:
        myBot.setSlotValue("main_subject", m_subject)
        get_graduation() #enables user to enter more information in one dialogue 
        return

    # Not a valid subject
    myBot.outputText("Das gewählte Studienfach ist nicht verfügbar.")
    myBot.setIndex(utter_ask_main_subject.getIndex())

def get_graduation():
    m_graduation = None
    if "graduation" in myBot.slotHashmap:
        m_graduation = myBot.slotHashmap["graduation"][0]

    # load the object form the Database
    main_subject_data = courseCollection.find_one({"main_subject": myBot.slotHashmap["main_subject"]})

    for grad in main_subject_data['graduation']:
        if m_graduation == grad:
            myBot.setIndex(utter_ask_sub_subject.getIndex())
            myBot.setSlotValue("graduation", m_graduation)
            get_sub_subject()
            return

    # check if we should throw an error
    if myBot.getIndex() > utter_ask_graduation.getIndex():
        myBot.outputText("Der gewählte Abschluss ist für das geswünschte Studienfach nicht verfügbar.")
        myBot.setIndex(utter_ask_graduation.getIndex())
        return


def get_sub_subject():
    m_subject = None

    if "subjects" in myBot.slotHashmap:
        m_subject = myBot.slotHashmap["subjects"][-1]

    sub_subject_list = []
    # load the object form the Database
    main_subject_data = courseCollection.find_one({"main_subject": myBot.slotHashmap["main_subject"]})
    if myBot.slotHashmap["graduation"] == "Bachelor":
        # test if array is empty
        if len(main_subject_data["bachelor_sub_subjects"]) == 0:
            myBot.setIndex(utter_ask_semester.getIndex())
            validate_semester_select()
            return

        for sub in main_subject_data["bachelor_sub_subjects"]:
            if m_subject == sub:
                myBot.setIndex(utter_ask_semester.getIndex())
                myBot.setSlotValue("sub_subject", m_subject)
                validate_semester_select()
                return
    else:
        # test if array is empty
        if len(main_subject_data["master_sub_subjects"]) == 0:
            myBot.setIndex(utter_ask_semester.getIndex())
            validate_semester_select()
            return

        for sub in main_subject_data["master_sub_subjects"]:
            if m_subject == sub:
                myBot.setIndex(utter_ask_semester.getIndex())
                myBot.setSlotValue("sub_subject", m_subject)
                validate_semester_select()
                return

    if myBot.getIndex() > utter_ask_sub_subject.getIndex():
        myBot.outputText("Das gewählte Nebenfach ist nicht mit dem Hauptfach kombinierbar.")
        myBot.slotHashmap["subjects"].pop(-1)
        myBot.setIndex(utter_ask_sub_subject.getIndex())
        return


def validate_semester_select():
    m_semester = None
    if "semester" in myBot.slotHashmap:
        m_semester = myBot.slotHashmap["semester"][0]

    main_subject_data = courseCollection.find_one({"main_subject": myBot.slotHashmap["main_subject"]})
    if m_semester < main_subject_data["max_semester"]:
        myBot.setIndex(utter_validate_study_data.getIndex())
        myBot.setSlotValue("semester", m_semester)
        myBot.setSlotValue("min_semester", main_subject_data["min_semester"])
        myBot.setSlotValue("max_semester", main_subject_data["max_semester"])
        return
    
    if myBot.getIndex() > utter_ask_semester.getIndex():
        myBot.outputText("Bitte geben sie eine Semesteranzahl zwischen " + 0 + " und " + main_subject_data["max_semester"] + " ein.")
        myBot.setIndex(utter_ask_semester.getIndex())
        return

def jump_to_selection(dia):
    myBot.setIndex(dia.getIndex())


def validate_max_semester_select():
    m_semester = None
    if "semester" in myBot.slotHashmap:
        m_semester = myBot.slotHashmap["semester"][-1]

    main_subject_data = courseCollection.find_one({"main_subject": myBot.slotHashmap["main_subject"]})

    if main_subject_data["min_semester"] < m_semester < main_subject_data["max_semester"]:
        myBot.setSlotValue("study_duration", m_semester)
        return
    
    myBot.outputText("Bitte geben sie eine Semesteranzahl zwischen " + main_subject_data["min_semester"] + " und " + main_subject_data["max_semester"] + " ein.")
    myBot.setIndex(utter_ask_semester.getIndex())

class User:
    restlp = 0

test = User()
def check_low_lp():
    if test.restlp > 15:
        jump_to_selection(utter_ask_for_changes_to_courseplan) 
# Sub Dialoge


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
jump_to_main_subject = Dialogue(action= lambda: jump_to_selection(utter_ask_main_subject))

utter_validate_study_data = Dialogue(botResponse="Sie befinden sich zurzeit im 1. Semester des {{graduation}} in {{main_subject}} mit {{sub_subject}}, ist das richtig?")
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

utter_ask_for_modules = Dialogue(botResponse="Welche Module haben sie bisher Abgeschlossen?")
user_intent_modules = Dialogue(userIntent="select_module", index=utter_ask_for_modules, subNodes=[action_get_modules])
user_intent_ask_for_help = Dialogue(userIntent="needs_help", index=utter_ask_for_modules, subNodes=[utter_give_flex_now, jumpt_to_models])

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
"Ihre Filterkriterien konnten leider keine Kurse finden. Bitte ändern sie diese."
"Es konnten keine weiteren Kurse gefunden werde. Wollen sie ihre Suchkriterien ändern?"

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
    utter_ask_for_modules, user_intent_modules, user_intent_ask_for_help,
    utter_ask_for_courses, user_validate_courses_no, user_intent_select_course,
    utter_ask_for_sws, user_intent_sws, action_get_sws,
    utter_finish_data_collection
])

# Select course
action_wants_information = Dialogue(action= lambda: get_information())

"Kurs {next_course} wurde dem Stundenplan hinzugefügt."
"Der Kurs {next_course} konnte leider nicht gefunden werden."

action_selects_course = Dialogue(action= lambda: select_course())

utter_found_course = Dialogue(botResponse="Für das Modul {{next_module}} werden die Kurse {{next_course_list}} angeboten. Wählen sie ob und welchen Kurs sie belegen wollen oder stellen sie Fragen zu den einzelnen Kursen für weitere Informationen.")
user_intent_ask_more_information = Dialogue(userIntent="wants_information", index=utter_found_course, subNodes=[action_wants_information])
user_intent_select_course = Dialogue(userIntent="accept_course", index=utter_found_course, subNodes=[action_selects_course])

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
action_jump_to_ask_change = Dialogue(action= lambda: jump_to_selection(utter_ask_what_changes))

utter_remove_course = Dialogue(botResponse="Sind sie sicher das der Kurs {{next_course}} von ihrem Stundenplan entfernt werden soll? Bitte beachten sie: {{warning}}")
user_wants_removal = Dialogue(userIntent="confim", index=utter_remove_course, subNodes=[action_remove_course])
user_reject_removal = Dialogue(userIntent="reject", index=utter_remove_course, subNodes=[action_jump_to_ask_change])

utter_ask_what_changes = Dialogue(botResponse="Geben sie an welcher Kurs aus ihrem Stundenplan gelöscht werden soll oder nennen sie einen Kurs um diesen hinzuzufügen.")
user_intent_add_course = Dialogue(userIntent="wants_course", index=utter_ask_what_changes, subNodes=[action_add_course])
user_intent_delete_course = Dialogue(userIntent="remove_course", index=utter_ask_what_changes, subNodes=[utter_remove_course])


## Main dialog
utter_ask_for_changes_to_courseplan = Dialogue(botResponse="Ihren Stundenplan können sie unter {{schedule_link}} einsehen. Möchten sie den Stundenplan übernehmen oder möchten sie Änderungen an diesem Vornehmen?")
user_reject_changes = Dialogue(userIntent="reject", index=utter_ask_for_changes_to_courseplan)
user_wants_changes = Dialogue(userIntent="confirm", index=utter_ask_for_changes_to_courseplan, subNodes=[utter_ask_what_changes])

# return stundenplan
utter_return_stundenplan = Dialogue(botResponse="Ihren fertigen Stundenplan können sie unter {{schedule_link}} einsehen.")


# Part two of the Bot selecting courses
Kursauswahl_Container = Dialogue(subNodes=[
    utter_found_course, user_intent_ask_more_information, user_intent_select_course,
    action_check_for_low_lp, utter_ask_for_aditional_courses, user_aditional_courses_dialog_no, user_aditional_courses_dialog_yes,
    utter_ask_for_changes_to_courseplan, user_reject_changes, user_wants_changes,
    utter_return_stundenplan
])


last_information = Dialogue(botResponse="{{add_information}}")
bot_finished = Dialogue(botResponse="Ich hoffe ich konnte ihnen weiterhelfen, vergessen sie nicht ihre Kurse im Studienportal zu belegen.")

myBot.addDialogue([intro, Datenerhebung_Container, action_finish_data_collection, Kursauswahl_Container, last_information, bot_finished])







def jumpToIntro():
    #myBot.jumpToDialog(main_graduation)
    return

mainDiaSub = Dialogue(subNodes=[main_graduation, sub_subject])
mainDia = Dialogue(subNodes=[intro, main_subject, mainDiaSub, ask_study_time, ask_main_subject])
testJump = Dialogue(action=lambda: jumpToIntro())

# Runs Main Dia everytime the user intents test
subDialogue1 = subDialogue(userIntent="test", dialogue=mainDia, standardDisabled=True)

# Sub dialogue can get Disabled like this
subDialogue1.disable()

# Or at initialisation like this with standardDiasabled = True
subDialogue2 = subDialogue(userIntent="test2", dialogue=mainDiaSub, standardDisabled=True)

def run_Rasa():
    subprocess.call(["rasa", "run" ,"--enable-api", "-m", "rasa-model/nlu-20230318-151247-cerulean-urn.tar.gz"])

myBot.addSubDialogue([subDialogue1])
myBot.addDialogue([mainDia, testJump])



def startEel():
    eel.init('gui')
    eel.start('main.html')


def startMain():
    myBot.mainLoop(startfunction=lambda: time.sleep(10))

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


# Alle Dialoge
#    "Ihr gewähltes Fach wird an der Universität nicht als Hauptfach angeboten."
#"Was ist ihr zweites Hauptfach/ ihre Nebenfächer?"
#    "Die ausgewählte Fächerkombination {main_subject} mit {sub_subject} ist leider nicht möglich."
#"Studieren sie {main_subject} im Bachelor oder Master Studiengang?"
#    "Der angegebene Abschluss {graduation} in {main_subject} wird an der Universität leider nicht angeboten."

# Alle Intents
"select_fach"
"select_semester"
"select_sws"
"needs_help"
"confirm"
"reject"
"select_module"
"select_course"

# Alle actions
"action_get_main_subject"
"action_sub_subject_needed"
"action_validate_sub_subject"
"action_validate_graduation"


#Kursauswahl

dia5a = Dialogue(botResponse="Please enter your name.")
dia6a = Dialogue(userIntent="yes")
dia7a = Dialogue(botResponse="Thanks for entering your name, your name is {{name}}.")
dia5b = Dialogue(botResponse="Sadge.")


dia1 = Dialogue(botResponse="Hi welcome to my useless Bot")
dia2 = Dialogue(botResponse="Do you want to enter your name?")
dia3a = Dialogue(userIntent="no", index=2, subNodes=[dia5b])
dia3b = Dialogue(userIntent="yes", index=2, subNodes=[dia5a, dia6a, dia7a])
dia6 = Dialogue(botResponse="Thanks for using the Bot. {{name}}")