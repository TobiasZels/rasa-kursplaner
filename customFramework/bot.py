import re

class Bot:
    mainRoutine = 0
    subRoutine = 0
    highestIndex = 0
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


            if needsInteraction:
                intent, slots = self.fetchFromNLU(input())
                success = False
                for dialogue in dialogueList:
                    # if the intent could be found then yay set the slot and continue
                    if dialogue.getUserIntent() == intent:
                        for elements in slots:
                            self.slotHashmap[list(elements.keys())[0]] = list(elements.values())[0]
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
                        
            for dialogue in dialogueList:
                if dialogue.getHasSlots() == True:
                    dialogue.fillSlotIntoResponse(self.slotHashmap)
                print(dialogue.getBotResponse())
                # Reset response to empty the filled slots again
                dialogue.resetResponse()

            # mainRoutine should only increase on successfull interaktions
            self.mainRoutine += 1

    def addDialogue(self, dialogueArray):

        # for each dialogue we add it to the hashmap
        for dialogue in dialogueArray:
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

    def fetchFromNLU(self, input):
        intent = "yes"
        slot = input
        slotname = "name"
        slots = [{slotname: slot}]
        return (intent, slots)

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

myBot = Bot()

dia5a = Dialogue(botResponse="Please enter your name.")
dia6a = Dialogue(userIntent="yes")
dia7a = Dialogue(botResponse="Thanks for entering your name, your name is {{name}}.")
dia5b = Dialogue(botResponse="Sadge.")


dia1 = Dialogue(botResponse="Hi welcome to my useless Bot")
dia2 = Dialogue(botResponse="Do you want to enter your name?")
dia3a = Dialogue(userIntent="no", index=2, subNodes=[dia5b])
dia3b = Dialogue(userIntent="yes", index=2, subNodes=[dia5a, dia6a, dia7a])
dia6 = Dialogue(botResponse="Thanks for using the Bot. {{name}}")




myBot.addDialogue([dia1, dia2, dia3a, dia3b, dia6])
myBot.mainLoop()
