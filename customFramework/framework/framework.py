import re
import subprocess
import os
import threading
import time
import requests
import json
import eel
import concurrent.futures
import csv as csv
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
        """
        Initializes a new dialogue

        Initializes a new dialogue, depending on what parameters are given it will serve different purposes.
        
        Parameters
        ----------
        index: Dialogue object | None
            Dialogue object that should appear at the same places.
        userIntent: string | None
            The intent that enables the user to continue that path in the dialogue
        action: function | None
            A function that gets called in the bot.
        botResponse: string | None
            The text the bot is supposed to send to the user.
        suNodes: Dialogue[] | None
            Dialogue objects that get called inside a second Bot instance.
        errorResponse: string | None
            Custom error messages, that gets send instead of the standard one. 
        ----------
        """
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
        """Get the dialogue index."""
        return self.index     
    
    def setIndex(self, index):
        self.index = index

    def getUserIntent(self):
        """Get the userIntent."""
        return self.userIntent

    def getBotResponse(self):
        """Get the bot response."""
        return self.botResponse 

    def getHasSlots(self):
        """Returns true if the dialogue has entity slots."""
        return self.hasSlots
    
    def setBotInstance(self, instance):
        self.botInstance = instance

    def getBotInstance(self):
        """Get the botInstance."""
        return self.botInstance

    def getFunction(self):
        """Returns the Dialogue function."""
        return self.action
    
    def getSubNodes(self):
        """Return the Sub Nodes."""
        return self.subNodes
    
    def setParent(self, parent):
        self.parent = parent
    
    def getParent(self):
        """Get the current parent."""
        return self.parent
    
    def getErrorResponse(self):
        """Get the errorResponse."""
        return self.errorResponse
    
    
    def fillSlotIntoResponse(self, slots):
        """
        Fills slots of the responses of the dialogue
        
        Parameters
        ----------
        slots: Dict(string, string)
            Slots that should get filled into bot messages.
        ----------
        """
        slotFields = re.findall("\{\{(.*?)\}\}", self.botResponse)
        for slot in slotFields:
            if slot in slots:
                slotValue = slots[slot]
                print(slotValue)
                if isinstance(slotValue, int):
                    slotValue = str(slotValue)
                self.botResponse = self.botResponse.replace("{{" + slot + "}}", str(slotValue))


    def resetResponse(self):
        """Resets the response to the template one, defined at the initialization."""
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
    dialogueHashmap = {}
    subRoutineList = []
    slotHashmap = {}
    ainput = None

    def __init__(self, slotHashmap={}, index = 0):
        """
        Initializes a new bot

        Initializes a new bot class.
        
        Parameters
        ----------
        slotHashmap: Dict(string, string) | None
           A dict that contains the slots of the user interaction.
        ----------
        """
        self.mainRoutine = index
        self.dialogueHashmap = {}
        self.slotHashmap = slotHashmap
        self.exit = False
    
    def mainLoop(self, startfunction=None):
        """
        Starts the bot main loop,
        
        Parameters
        ----------
        startfunction: function | None
           Runs a function once at the start of the function.
        ----------
        """
        if not startfunction == None:
            startfunction()
        while(not self.exit):
            # if the dialogue went outside the Hashmap end the loop/restart the loop
            if not self.mainRoutine in self.dialogueHashmap:
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

                input = self.awaitInput()
                intent, slots = self.fetchFromNLU(input)
                success = False
                for dialogue in dialogueList:
                    self.logConversationData(input, intent, slots, dialogue.getUserIntent())

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
                            continue
                            # then go back one step so the user sees the last question again
  
                # if even in the sub routibe nothing could be found then we need to return an error
                if dialogueList[0].getErrorResponse():
                    self.outputText(dialogueList[0].getErrorResponse())
                    continue

                self.outputText("Ich konnte sie leider nicht verstehen, versuchen sie es erneut.")
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

    def logConversationData(self, input, intent, slots, dialogueIntent):
        """
        Safes the Log data to a csv File
        
        Parameters
        ----------
        input: string
            The userinput
        intent: string
            The intent the userinput got rated at from the NLU.
        slots: Dict(string, string)
            The slots the NLU extracted from the userinput.
        dialogueIntent: string
            The intents the Bot expected at that position in the dialogue.
        ----------
        """
        row = {'input': input, 'intent': intent, 'slots': slots, 'expected_intents': dialogueIntent}
        with open('logFiles/nlu.csv', 'a', newline='') as f:
            dictwriter_object = csv.DictWriter(f, fieldnames=['input', 'intent', 'slots', 'expected_intents'])
            dictwriter_object.writerow(row)
            f.close()

    def addDialogue(self, dialogueArray):
        """
        Adds the Dialogue objects to the Bot.
        
        Parameters
        ----------
        dialogueArray: Dialogue[] | None
            All the Dialogue objects that will get used by the Bot.
        ----------
        """
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
        """
        Adds the sub Dialogue object to the Bot.
        
        Parameters
        ----------
        dialogueList: subDialogue[] | None
            All the sub Dialogue objects that will get used by the Bot.
        ----------
        """
        self.subRoutineList = dialogueList

    def setNLU(self, url):
        self.NLUUrl = url

    def setSlotValue(self, key,  value):
        self.slotHashmap[key] = value

    def deleteSlotValue(self, key):
        del self.slotHashmap[key]
    
    def setIndex(self, index):
        self.mainRoutine = index

    def hasExited(self):
        """Returns if the mainLoop has exited."""
        return self.exit
    
    def setExited(self, exited):
        self.exit = exited


    def jumpToDialog(self, dialog, offset=-1):
        """
        Jumps to a cetrain Dialog object.
        
        Parameters
        ----------
        dialog: Dialogue
            The Dialogue the bot should jump too.
        offset: integer | -1
            If the Bot bugs and jumps too far set this to 0.
        ----------
        """
        dialog.getBotInstance().setIndex(dialog.getIndex() + offset)

        if dialog.getBotInstance().hasExited():
            dialog.getBotInstance().setExited(False)
            dialog.getBotInstance().mainLoop()
        
        # Iterate to the outmost Instance
        if not dialog.getParent() == None:
            dialog.getParent().getBotInstance().jumpToDialog(dialog.getParent(), 0)

        # Set the index


    def getIndex(self):
        """Returns the index of the bot."""
        return self.mainRoutine
    

    # EEL functions
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
        """
        Sends the user message to the NLU.
        
        Parameters
        ----------
        input: string
            The userinput that gets send to the NLU.
        ----------
        """
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