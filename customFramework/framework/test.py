from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.pagesizes import letter



def simple_table(tableDict = dict()):
    doc = SimpleDocTemplate("simple_table.pdf", pagesize=letter)
    flowables = []
    print(tableDict['mo8'])
    data = [
            ["Uhrzeit", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"],
            ["8 - 10", tableDict.get('mo8', ""), tableDict.get('di8', ""), tableDict.get('mi8', ""), tableDict.get('do8', ""), tableDict.get('fr8', "")],
            ["10 - 12", tableDict.get('mo10', ""), tableDict.get('di10', ""), tableDict.get('mi10', ""), tableDict.get('do10', ""), tableDict.get('fr10', "")],
            ["12 - 14", tableDict.get('mo12', ""), tableDict.get('di12', ""), tableDict.get('mi12', ""), tableDict.get('do12', ""), tableDict.get('fr12', "")],
            ["14 - 16", tableDict.get('mo14', ""), tableDict.get('di14', ""), tableDict.get('mi14', ""), tableDict.get('do14', ""), tableDict.get('fr14', "")],
            ["16 - 18", tableDict.get('mo16', ""), tableDict.get('di16', ""), tableDict.get('mi16', ""), tableDict.get('do16', ""), tableDict.get('fr16', "")],
            ["18 - 20", tableDict.get('mo18', ""), tableDict.get('di18', ""), tableDict.get('mi18', ""), tableDict.get('do18', ""), tableDict.get('fr18', "")]
            ]
    tbl = Table(data)
    flowables.append(tbl)
    doc.build(flowables)


simple_table(dict({"mo8": "Test", "do8": "Donnerstages"}))

