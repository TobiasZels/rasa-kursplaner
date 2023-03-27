from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.pagesizes import letter



def simple_table(tableDict = dict()):
    doc = SimpleDocTemplate("Zeitplan/simple_table.pdf", pagesize=letter)
    flowables = []
    print(tableDict['mo8'])
    data = [
            ["Uhrzeit", "Montag"],
            ["8 - 10", tableDict.get('mo8', "")],
            ["10 - 12", tableDict.get('mo10', "")],
            ["12 - 14", tableDict.get('mo12', "")],
            ["14 - 16", tableDict.get('mo14', "")],
            ["16 - 18", tableDict.get('mo16', "")],
            ["18 - 20", tableDict.get('mo18', "")]
            ["Uhrzeit", "Dienstag"],
            ["8 - 10",  tableDict.get('di8', "")],
            ["10 - 12", tableDict.get('di10', "")],
            ["12 - 14", tableDict.get('di12', "")],
            ["14 - 16", tableDict.get('di14', "")],
            ["16 - 18", tableDict.get('di16', "")],
            ["18 - 20", tableDict.get('di18', "")]
            ["Uhrzeit", "Mittwoch"],
            ["8 - 10",  tableDict.get('mi8', "")],
            ["10 - 12", tableDict.get('mi10', "")],
            ["12 - 14", tableDict.get('mi12', "")],
            ["14 - 16", tableDict.get('mi14', "")],
            ["16 - 18", tableDict.get('mi16', "")],
            ["18 - 20", tableDict.get('mi18', "")]
            ["Uhrzeit", "Donnerstag"],
            ["8 - 10",  tableDict.get('do8', "")],
            ["10 - 12", tableDict.get('do10', "")],
            ["12 - 14", tableDict.get('do12', "")],
            ["14 - 16", tableDict.get('do14', "")],
            ["16 - 18", tableDict.get('do16', "")],
            ["18 - 20", tableDict.get('do18', "")]
            ["Uhrzeit", "Freitag"]
            ["8 - 10",  tableDict.get('fr8', "")],
            ["10 - 12", tableDict.get('fr10', "")],
            ["12 - 14", tableDict.get('fr12', "")],
            ["14 - 16", tableDict.get('fr14', "")],
            ["16 - 18", tableDict.get('fr16', "")],
            ["18 - 20", tableDict.get('fr18', "")]


















            ]
    tbl = Table(data)
    flowables.append(tbl)
    doc.build(flowables)


simple_table(dict({"mo8": "Test", "do8": "Donnerstages"}))

