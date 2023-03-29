# rasa-kursplaner
Projekt für Kurs Algorithmen für MMI WS 2022/23

# Installation
## Python Packages
```console
pip install bs4 && pip install pymongo && pip install eel && pip install reportlab
```
## Zusätzliche Programme
Mongo DB:
https://www.mongodb.com/docs/manual/installation/

Rasa:
https://rasa.com/docs/rasa/installation/installing-rasa-open-source/

## Starten des Kursplaner Bots
1. Starten von MongoDB
2. Datenbank importieren mit
```console
cd customFramework/framework
python database_creation.py
```
3. (optional) Rasa trainieren mit 
```console
cd Rasa
rasa train nlu
```
4. Chatbot starten mit
```console
cd customFramework/framework
python bot.py
```
