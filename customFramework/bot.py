import re
import requests
import json


class Dialogue:
    index = None
    userIntent = None
    action = None
    botResponse = None
    templateResponse = None
    hasSlots = False
    subNodes = []

    def __init__(self, index=None, userIntent=None, action=None, botResponse=None, subNodes=None):
        self.index = index
        self.userIntent = userIntent
        self.action = action
        self.botResponse = botResponse
        self.subNodes = subNodes
        self.templateResponse = botResponse
        if not botResponse == None:
            slotFields = re.findall("\{\{(.*?)\}\}", botResponse)
            if len(slotFields) > 0:
                self.hasSlots = True

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
    
    def getFunction(self):
        return self.action
    
    def getSubNodes(self):
        return self.subNodes
    
    def fillSlotIntoResponse(self, slots):
        slotFields = re.findall("\{\{(.*?)\}\}", self.botResponse)
        for slot in slotFields:
            if slot in slots:
                self.botResponse = self.botResponse.replace("{{" + slot + "}}", slots[slot])

    def resetResponse(self):
        self.botResponse = self.templateResponse


class Bot:
    mainRoutine = 0
    subRoutine = 0
    highestIndex = 0
    NLUUrl = "http://localhost:5005/model/parse"
    exit = False
    # What i learned in Codinginterviews if you have no clue how to solve a task just throw a random
    # Hashmap at it ^_^
    dialogueHashmap = {}
    slotHashmap = {}

    def __init__(self, slotHashmap={}):
        self.dialogueHashmap = {}
        self.slotHashmap = slotHashmap
        self.exit = False
    
    def mainLoop(self):
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

                # if even in the sub routibe nothing could be found then we need to return an error TODO
                print("I didn't understand your message")
                continue

            # Print out the bot message and fill slots at runtime      
            for dialogue in dialogueList:
                if dialogue.getHasSlots() == True:
                    dialogue.fillSlotIntoResponse(self.slotHashmap)

                if not dialogue.getBotResponse() == None:   
                    print(dialogue.getBotResponse())
                # Reset response to empty the filled slots again
                dialogue.resetResponse()

            # mainRoutine should only increase on successfull interaktions
            self.mainRoutine += 1

    def addDialogue(self, dialogueArray):

        # for each dialogue we add it to the hashmap
        for dialogue in dialogueArray:
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

    def setSlotValue(self, key,  value):
        self.slotHashmap[key] = value
    
    def setIndex(self, index):
        self.mainRoutine = index -1

    def getIndex(self):
        return self.mainRoutine

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


myBot = Bot()


def get_main_subject():
    m_subject = myBot.slotHashmap["subjects"][0]

    if m_subject == "Medieninformatik":
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

    if m_graduation == "Bachelor":
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

    if m_subject == "Informationswissenschaft":
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
next_dialog = Dialogue(botResponse="Sie verfolgen {{main_subject}} mit {{sub_subject}} im {{graduation}}?")
next_dialog_yes = Dialogue(userIntent="confirm", index=next_dialog)
next_dialog_no = Dialogue(userIntent="reject", index=next_dialog, subNodes=[jump_to_main_subject])

myBot.addDialogue([intro, main_subject, ask_main_subject, action_get_main_subject, main_graduation, ask_graduation, action_get_graduation, sub_subject, ask_sub_subject, action_get_sub_subject,  next_dialog,next_dialog_yes ,next_dialog_no])
myBot.mainLoop()
