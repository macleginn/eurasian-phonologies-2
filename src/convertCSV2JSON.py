import csv
import json

def clear(s):
    return s.strip(' \n\t').replace('\u0361', '').replace('\u2009', '')

contributorsReplacementDict = {
    'Андрей Никулин, ojovemlouco@gmail.com': 'André Nikulin, ojovemlouco@gmail.com',
    'Дмитрий Николаев, dsnikolaev@gmail.com': 'Dmitry Nikolayev, dsnikolaev@gmail.com'
}

def convert2JSON(path):
    lang_dic = {}
    with open(path, 'r', encoding='utf-8') as inp:
        records = list(csv.reader(inp, delimiter='\t'))[1:]
    for i in range(len(records)):
        idiom_type = clear(records[i][5])
        name    = clear(records[i][1])
        code    = clear(records[i][2])
        lang_id = name + "#" + str(i)
        lat     = clear(records[i][3])
        lon     = clear(records[i][4])
        family  = clear(records[i][6])
        group   = clear(records[i][7])
        cons    = clear(records[i][10]).split(', ')
        vows    = clear(records[i][11]).split(', ')
        tones   = clear(records[i][12]).split(', ')
        inv     = cons + vows
        source  = clear(records[i][8])
        syllab  = clear(records[i][13])
        cluster = clear(records[i][14])
        finals  = clear(records[i][15])
        comment = clear(records[i][16]).replace('\n', ' ')
        contr   = clear(records[i][17])
        if contr in contributorsReplacementDict:
            contr = contributorsReplacementDict[contr]

        lang_dic[lang_id] = {
            "code": code,
            "type": idiom_type,
            "name": name,
            "coords": [lat, lon],
            "gen": [family, group],
            "inv": inv,
            "cons": cons,
            "vows": vows,
            "tones": tones,
            "syllab": syllab,
            "cluster": cluster,
            "finals": finals,
            "source": source,
            "comment": comment,
            "contr": contr
        }
    return lang_dic

with open("dbase/phono_dbase.json", "w", encoding = "utf-8") as out:
    json.dump(convert2JSON("dbase/ffli-dbase.csv"), out, indent = 4, ensure_ascii = False)