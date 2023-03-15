import re
import subprocess
import os
import threading
import requests
import json
from pymongo import MongoClient

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
                intent, slots = self.fetchFromNLU(input())
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
        pass

    def fetchFromNLU(self, input):

        object = {'text': input}
        slots = {}

        # Post request to the Rasa NLU model server
        response = requests.post(self.NLUUrl, json=object)
        resonseObject = json.loads(response.text)
        # Grab the intent 
        intent = resonseObject["intent"]["name"]
        # Grab all the Entities to fill the slots
        for entity in resonseObject["entities"]:
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

def get_main_subject():
    m_subject = myBot.slotHashmap["subjects"][0]
    
    if not courseCollection.find_one({"main_subject": m_subject}) == None:
        myBot.setSlotValue("main_subject", m_subject)
        get_graduation()
        return

    # Not a valid subject
    print("Das gewählte Studienfach ist nicht verfügbar.")
    myBot.setIndex(main_subject.getIndex())


def get_graduation():
    m_graduation = None
    if "graduation" in myBot.slotHashmap:
        m_graduation = myBot.slotHashmap["graduation"][0]


    # load the object form the Database
    main_subject_data = courseCollection.find_one({"main_subject": myBot.slotHashmap["main_subject"]})

    for grad in main_subject_data['graduation']:
        if m_graduation == grad:
            myBot.setIndex(sub_subject.getIndex())
            myBot.setSlotValue("graduation", m_graduation)
            get_sub_subject()
            return

    if myBot.getIndex() > ask_graduation.getIndex():
        print("Der gewählte Abschluss ist für das geswünschte Studienfach nicht verfügbar.")
        myBot.setIndex(main_graduation.getIndex())
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
            myBot.setIndex(next_dialog.getIndex())
            return

        for sub in main_subject_data["bachelor_sub_subjects"]:
            if m_subject == sub:
                myBot.setIndex(next_dialog.getIndex())
                myBot.setSlotValue("sub_subject", m_subject)
                return
    else:
        # test if array is empty
        if len(main_subject_data["master_sub_subjects"]) == 0:
            myBot.setIndex(next_dialog.getIndex())
            return

        for sub in main_subject_data["master_sub_subjects"]:
            if m_subject == sub:
                myBot.setIndex(next_dialog.getIndex())
                myBot.setSlotValue("sub_subject", m_subject)
                return

    if myBot.getIndex() > sub_subject.getIndex():
        print("Das gewählte Nebenfach ist nicht mit dem Hauptfach kombinierbar.")
        myBot.slotHashmap["subjects"].pop(-1)
        myBot.setIndex(sub_subject.getIndex())
        return

def jump_main_subject():
    myBot.setIndex(ask_main_subject.getIndex())

def validate_semester_select():
    "Bitte geben sie eine gültige Semesterzahl zwischen {min_semester} und {max_semester} ein."

def validate_max_semester_select():
    "Bitte geben sie eine gültige Semesterzahl zwischen {min_semester} und {max_semester} ein."

def seach_course_list():
    ""

dia5a = Dialogue(botResponse="Please enter your name.")
dia6a = Dialogue(userIntent="yes")
dia7a = Dialogue(botResponse="Thanks for entering your name, your name is {{name}}.")
dia5b = Dialogue(botResponse="Sadge.")


dia1 = Dialogue(botResponse="Hi welcome to my useless Bot")
dia2 = Dialogue(botResponse="Do you want to enter your name?")
dia3a = Dialogue(userIntent="no", index=2, subNodes=[dia5b])
dia3b = Dialogue(userIntent="yes", index=2, subNodes=[dia5a, dia6a, dia7a])
dia6 = Dialogue(botResponse="Thanks for using the Bot. {{name}}")

# Sub Dialoge
jump_to_main_subject = Dialogue(action= lambda: jump_main_subject())


# Main Dialoge
intro = Dialogue(botResponse="Willkommen beim Kursplaner, im nachfolgenden werde ich sie bei der Auswahl ihrer Kurse für das nachfolgende Semester unterstützen.")
main_subject = Dialogue(botResponse="Welches Fach studieren sie aktuell als Hauptfach?")
ask_main_subject = Dialogue(userIntent="select_fach")
action_get_main_subject = Dialogue(action=lambda: get_main_subject())
main_graduation = Dialogue(botResponse="Welchen Abschluss verfolgen sie?")
ask_graduation = Dialogue(userIntent="select_graduation")
action_get_graduation = Dialogue(action=lambda: get_graduation())
sub_subject = Dialogue(botResponse="Was ist ihr Nebenfach?")
ask_sub_subject = Dialogue(userIntent="select_fach")
action_get_sub_subject = Dialogue(action=lambda: get_sub_subject())
ask_study_time = Dialogue(botResponse="Für welches Semester möchten sie einen Stundenplan erstellen?")
user_select_semester = Dialogue(userIntent="select_semester")
action_get_sub_subject = Dialogue(action=lambda: validate_semester_select())
next_dialog = Dialogue(botResponse="Sie befinden sich zurzeit im 1. Semester des {{graduation}} in {{main_subject}} mit {{sub_subject}}, ist das richtig?")
next_dialog_yes = Dialogue(userIntent="confirm", index=next_dialog)
next_dialog_no = Dialogue(userIntent="reject", index=next_dialog, subNodes=[jump_to_main_subject])
ask_study_time = Dialogue(botResponse="Bis zu welchem Semester wollen Sie ihr Studium abschließen, empfohlen wird für {{main_subject}}  {{min_semester}} Semester mit einer maximalen Studiendauer von {{max_semester}} Semestern.")
user_select_semester = Dialogue(userIntent="select_semester")
action_get_sub_subject = Dialogue(action=lambda: validate_max_semester_select())
ask_study_time = Dialogue(botResponse="Welche Module haben sie bisher Abgeschlossen?")
user_select_semester = Dialogue(userIntent="select_module")
#"Ihre bereits abgeschlossenen Module können sie unter (Flex-Now Link) einsehen."
ask_study_time = Dialogue(botResponse="Haben sie Kurse aus noch nicht abgeschlossenen Modulen bereits besucht?")
user_select_semester = Dialogue(userIntent="select_course")
ask_study_time = Dialogue(botResponse="Wie viel Zeit möchten sie für ihr Studium dieses Semester aufbringen, um das Studium in der gewünschten Zeit abzuschließen werden {sws_empf} SWS empfohlen.")
user_select_semester = Dialogue(userIntent="select_sws")
ask_study_time = Dialogue(botResponse="Bitte warten sie während ich für Sie nach Kursen suche...")
action_get_sub_subject = Dialogue(action=lambda: seach_course_list())

# Idea use empty Dialogue Objects as containers and only us


#myBot.addDialogue([intro, main_subject, 
#                   ask_main_subject,
#                   action_get_main_subject, main_graduation, 
#                   ask_graduation, action_get_graduation, 
#                   sub_subject, ask_sub_subject, action_get_sub_subject,  
#                   next_dialog,next_dialog_yes ,next_dialog_no])


def jumpToIntro():
    #myBot.jumpToDialog(main_graduation)
    return

mainDiaSub = Dialogue(subNodes=[main_graduation, sub_subject])
mainDia = Dialogue(subNodes=[intro, main_subject, mainDiaSub, ask_study_time, ask_sub_subject])
testJump = Dialogue(action=lambda: jumpToIntro())

# Runs Main Dia everytime the user intents test
subDialogue1 = subDialogue(userIntent="test", dialogue=mainDia, standardDisabled=True)

# Sub dialogue can get Disabled like this
subDialogue1.disable()

# Or at initialisation like this with standardDiasabled = True
subDialogue2 = subDialogue(userIntent="test2", dialogue=mainDiaSub, standardDisabled=True)

def run_Rasa():
    subprocess.call(["rasa", "run" ,"--enable-api", "-m", "rasa-model/model.tar.gz"])

myBot.addSubDialogue([subDialogue1])
myBot.addDialogue([mainDia, testJump])
subprocess.run(["ls", "-l"])
t = threading.Thread(target=run_Rasa)
s = threading.Thread(target=myBot.mainLoop, args=())
t.start()
s.start()

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

# Alle Dialoge
"Es konnten keine weiteren Kurse gefunden werde. Wollen sie ihre Suchkriterien ändern?"
"Ihre Filterkriterien konnten leider keine Kurse finden. Bitte ändern sie diese."
"Für das Modul {next_module} werden die Kurse {next_course_list} angeboten. Wählen sie ob und welchen Kurs sie belegen wollen oder stellen sie Fragen zu den einzelnen Kursen für weitere Informationen. "
"Der Kurs {next_course} konnte leider nicht gefunden werden."
"Kurs {next_course} wurde dem Stundenplan hinzugefügt."
"Der Kurs {next_course} konnte leider nicht gefunden werden."
"Für das Modul {next_module} wird der Kurs {next_course},  {speciality_text}, angeboten. Geben sie an ob sie diesen Kurs belegen wollen oder stellen sie Fragen zu dem Kurs für weitere Informationen."
"Für den Abschluss ihres Studiums benötigen sie zusätzlich nur noch {lp_left}, möchten sie einen weiteren Kurs belegen um diese lp zu erreichen?"
"Ihren Stundenplan können sie unter {schedule_link} einsehen. Möchten sie den Stundenplan übernehmen oder möchten sie Änderungen an diesem Vornehmen?"
"Geben sie an welcher Kurs aus ihrem Stundenplan gelöscht werden soll oder nennen sie einen Kurs um diesen hinzuzufügen. "
"Der angegebene Kurs existiert nicht."
"Der Kurs {next_course} wurde dem Stundenplan hinzugefügt."
"Sind sie sicher das der Kurs {next_course} von ihrem Stundenplan entfernt werden soll? Bitte beachten sie: {warning}"
"Ihren Stundenplan können sie unter {schedule_link} einsehen."

"{add_information}"
"Ich hoffe ich konnte ihnen weiterhelfen, vergessen sie nicht ihre Kurse im Studienportal zu belegen."
# Alle Intents
"wants_information"
"accept_course"
"denie"
"wants_studenplan"
# Alle actions