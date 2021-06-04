
import requests
import time
import spacy
nlp = spacy.load("en_core_web_sm")

def main():
    pass

def execQuery(query, url):
    req = requests.get(url, params={'query': query, 'format': 'json'})
    if req.status_code == 429:
        print('Too many requests, retrying....')
        time.sleep(5)
        return execQuery(query, url)
    else:
        results = req.json()
    try:
        var = results['head']['vars'][0]
    except:
        return results['boolean']
    output = []
    for result in results['results']['bindings']:
        output.append(result[var]['value'])
    
    #print(output)
    return output
    
def getEntPropIds(entity, prop):
    url = 'https://www.wikidata.org/w/api.php'
    params = {'action':'wbsearchentities', 
          'language':'en',
          'type' : 'item',
          'format':'json'}
    
    params['search'] = entity
    json = requests.get(url,params).json()
    
    p_ids = getIds(json)
    
    params['type'] = 'property'
    params['search'] = prop
    json = requests.get(url,params).json()
    
    q_ids = getIds(json)
    
    #Return and limit the entity list to 2.
    return p_ids[:2], q_ids[:2]

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
    ent, pred = getEntPred(question)
    w = question.split()[0].lower()
    if debug:
        print(w, " | ", ent, " | ", pred)
    if ent == '' or pred == '':
        print('Could not find entities or predicates.')
    else:
        p_ids, q_ids = getEntPropIds(ent, pred)
        if debug:
            print(p_ids, q_ids)

        return getAnswer(w, p_ids, q_ids)


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
                
            query = "SELECT ?xLabel WHERE {wd:" + p_id + " wdt:" + q_id + " ?x. SERVICE wikibase:label { bd:serviceParam wikibase:language '[AUTO_LANGUAGE],en'. }}"
            query2 = "SELECT ?xLabel WHERE {?x wdt:" + q_id + " wd:" + p_id + ". SERVICE wikibase:label { bd:serviceParam wikibase:language '[AUTO_LANGUAGE],en'. }}"
            #print(query)
            #results = requests.get(url, params={'query': query, 'format': 'json'}).json()
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
                
def getEntPred(question):
    parse = nlp(question)
    #displacy.render(parse, jupyter=True, style="ent")
    #displacy.render(parse, jupyter=True, style="dep")
    
    ws = ['who', 'what', 'when', 'which', 'where', 'how']
    ent = []
    pred = []
    
    for word in parse:
        if word.dep_ == 'ROOT':
            #print(word.text)
            for child in word.subtree:
                if child.dep_ == 'advmod' and child.lemma_.lower() not in ws:
                    pred = phrase(child)
                elif child.dep_ == 'nsubj' and child.orth_.lower() not in ws:
                    ent = phrase(child)
                    children  = [sub for sub in child.children]
                    for sub in children:
                        #print(sub)
                        if sub.dep_ == 'prep':
                            #print(sub)
                            ent = phrase([subsub for subsub in sub.children if subsub.dep_ == 'pobj'][0])
                            pred = [child.orth_]
                elif child.dep_ == 'dobj' and child.i < word.i:
                    pred = phrase(child)
                elif child.dep_ == 'dobj' and child.i > word.i:
                    ent = phrase(child)
                elif child.dep_ == 'agent':
                    agent = [agent for agent in child.children][0]
                    #print(agent)
                    ent = phrase(agent)
    
    if len(pred) == 0:
        pred = [word.orth_ for word in parse if word.dep_ == 'ROOT']
    #print(ent, pred)
    ent = " ".join(ent)
    pred = " ".join(pred)
    #print(ent, pred)
    
    
    return ent, pred

def phrase(word):
    compound = [word]
    for child in word.subtree:
        if child.dep_ == 'compound':
            compound.append(child)
    
    compound.sort(key= lambda x: x.i)
    compound = [word.orth_ for word in compound]
    
    return compound

if __name__ == '__main__':
    main()