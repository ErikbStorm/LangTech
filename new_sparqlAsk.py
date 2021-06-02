import pickle
import requests
import time
import json
import spacy
from spacy import displacy
from Levenshtein import distance as lev
nlp = spacy.load("en_core_web_sm")

def main():
    questions = [#'Who are the screenwriters for The Place Beyond The Pines?',
                #'Who were the composers for Batman Begins?',
                #'What awards did Frozen receive?',
                #'How many awards did Frozen receive?',
                #'How old is Jim Carrey?',
                #'Which company distributed Avatar?',
                #'Who is the mommy of Leonardo di Caprio?',
                #"What is James Bond catchphrase?",
                "Where did Brad Pitt go to school?"]
                
                'Which company distributed Avatar?',
                'Who is Leonardo di Caprio?',
                "What is James Bond catchphrase?"]

    links = readJson('property_links.json')
    for question in questions:
        print(question)
        answer = ask(question, links, debug=True)
        print(answer)

def ask(question, links, debug=False):
    parse = nlp(question)
    ent = getEnt(parse)
    if len(ent) > 0:
        search_props = removeStopWords(question, ent[0])
        print("Search properties: " , search_props)
        ent_ids = getEntIds(ent)

        linked_prop = getBestProp(search_props, links)
        print("Linked properties: " , linked_prop)

        properties = getProperties(ent_ids[0])

        for p, v in properties.items():
            print(p, " : ", v)

        return properties[linked_prop]
    else:
        print('No entities found!')
        return [0]

def execQuery(query, url):
    req = requests.get(url, params={'query': query, 'format': 'json'})
    if req.status_code == 429:
        print('Too many requests, retrying....')
        time.sleep(5)
        return execQuery(query, url)
    else:
        results = req.json()

    return results
    
def getEntIds(entity):
    url = 'https://www.wikidata.org/w/api.php'
    params = {'action':'wbsearchentities', 
          'language':'en',
          'type' : 'item',
          'format':'json'}
    
    params['search'] = entity
    json = requests.get(url,params).json()
    
    p_ids = getIds(json)
    return p_ids[:5]

def getIds(json):
    ids = []
    try:
        #print(json)
        for result in json['search']:
            ids.append((result['id'], result['label']))
        return ids
    except:
        print('Error Occurred')
        print(json)

def readJson(filename):
    with open(filename, 'r') as f:
        return json.load(f)
                
def getEnt(parse):
    entity = list()

    for word in parse[1:]:
        if word.text.istitle() or word.text[0].isdigit():
            entity.append(int(word.i))
    return ' '.join([word.text for word in parse[entity[0]:(entity[-1]+1)]])

def removeStopWords(question, ent):
    question = question.replace(ent, '')
    no_stop_words = [word for word in nlp(question)
                        if not word.is_stop and word.pos_ != 'PUNCT' 
                        and word.text != ' ']
    print(no_stop_words)

    return no_stop_words


def getBestProp(search_props, links):
    same_prop_counts = {}
    for prop, related_props in links.items():
        #print(prop, related_props)
        same_props = [search_prop.lemma_ for search_prop in search_props if search_prop.lemma_ in related_props]
        same_prop_amount = len(same_props)
        same_prop_counts[same_prop_amount] = prop

    #print(same_prop_counts)
    max_key = max(same_prop_counts.keys())

    return same_prop_counts[max_key]


def getAnswer(search_pred, properties):
    distances = {}
    for property, values in properties.items():
        distance = lev(property, search_pred)
        distances[distance] = (property, values)

    id_with_lowest_distance = min(distances.keys())

    return distances[id_with_lowest_distance]

def getProperties(ent_id):
    print(ent_id)
    url = 'https://query.wikidata.org/sparql'

    query = ''' SELECT ?wdLabel ?ps_Label{
                VALUES (?company) {(wd:'''+ ent_id[0] +''')}
                
                ?company ?p ?statement .
                ?statement ?ps ?ps_ .
                
                ?wd wikibase:claim ?p.
                ?wd wikibase:statementProperty ?ps.
                
                
                SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
                } ORDER BY ?wd ?statement ?ps_
                '''

    answer = execQuery(query, url)

    #print(answer.keys())

    prop, value = answer['head']['vars']

    output = {}
    for row in answer['results']['bindings']:
        if row[prop]['value'] in output:
            output[row[prop]['value']].append(row[value]['value'])
        else:
            output[row[prop]['value']] = [row[value]['value']]
    
    #print(output)

    return output


if __name__ == '__main__':
    main()