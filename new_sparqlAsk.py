import pickle
import requests
import time
import spacy
from spacy import displacy
from Levenshtein import distance as lev
from spacy.pipeline import EntityRuler

nlp = spacy.load("en_core_web_lg")
with open('patterns.pickle')

ruler = EntityRuler(nlp)
ruler.add_patterns(pattern)



def main():
    questions = ['Who are the screenwriters for The Place Beyond The Pines?', 
                'Who were the composers for Batman Begins?',
                'What awards did Frozen receive?',
                'How many awards did Frozen receive?']
    for question in questions:
        print(question)
        answer = ask(question, debug=True)
        print(answer)

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

def ask(question, debug=False):
    parse = nlp(question)
    ent = getEnt(parse)
    prop = removeStopWords(question, ent[0])
    #print("Properties: " + prop)
    ent_ids = getEntIds(ent)

    properties = getProperties(ent_ids[0])

    return getAnswer(prop, properties)

    return 0

    if "how many" in question.lower():
        w = "how many"
    else:
        w = question.split()[0].lower()
    if debug:
        print(w, " | ", ent)
    if ent == '':
        print('Could not find entities.')
    else:
        ent_ids = getEntIds(ent)
        getPredicates(ent_ids[0])
        if debug:
            print(p_ids, q_ids)

        return getAnswer(w, p_ids, q_ids)
    return ent

def getAnswer(w, p_ids, q_ids):
    url = 'https://query.wikidata.org/sparql'
    
    if w == 'when':
        q_ids = [(q_id, q_label) for q_id, q_label in q_ids if 'date' in q_label.lower().split()]
    elif w == 'where':
        q_ids = [(q_id, q_label) for q_id, q_label in q_ids if 'place' in q_label.lower().split()]
    
    for p_id_list in p_ids:
        p_id = p_id_list[0]
        for q_id_list in q_ids:
            q_id = q_id_list[0]
            
            if (w == "how many"):
                query = "SELECT (COUNT(?x) as ?count) WHERE {wd:" + p_id + " wdt:" + q_id + " ?x. SERVICE wikibase:label { bd:serviceParam wikibase:language '[AUTO_LANGUAGE],en'. }}"
                query2 = "SELECT (COUNT(?x) as ?count) WHERE {?x wdt:" + q_id + " wd:" + p_id + ". SERVICE wikibase:label { bd:serviceParam wikibase:language '[AUTO_LANGUAGE],en'. }}"
            else:
                query = "SELECT ?xLabel WHERE {wd:" + p_id + " wdt:" + q_id + " ?x. SERVICE wikibase:label { bd:serviceParam wikibase:language '[AUTO_LANGUAGE],en'. }}"
                query2 = "SELECT ?xLabel WHERE {?x wdt:" + q_id + " wd:" + p_id + ". SERVICE wikibase:label { bd:serviceParam wikibase:language '[AUTO_LANGUAGE],en'. }}"
            

            try:
                answer = execQuery(query, url)
                if len(answer) != 0:
                    return answer
                else:
                    answer = execQuery(query2, url)
                    if len(answer) != 0:
                        return answer
            except:
                query = "SELECT ?label WHERE {wd:" + p_id + " wdt:" + q_id + " ?label.}"
                answer = execQuery(query, url)
                if len(answer) != 0:
                    return answer


def getEnt(parse):
    entity = list()

    for word in parse[1:]:
        if word.text.istitle() or word.text[0].isdigit():
            entity.append(int(word.i))
    return ' '.join([word.text for word in parse[entity[0]:(entity[-1]+1)]])

def removeStopWords(question, ent):
    question = question.replace(ent, '')
    no_stop_words = [word.text for word in nlp(question) 
                        if not word.is_stop and word.pos_ != 'PUNCT' 
                        and word.text != ' ']
    print(no_stop_words)

    return " ".join(no_stop_words)


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