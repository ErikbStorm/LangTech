import requests
import time
import json
import spacy
from Levenshtein import distance as lev

nlp = spacy.load("en_core_web_sm")
#ruler = nlp.add_pipe("entity_ruler")
#ruler.from_disk("patterns.jsonl")

# Global debug toggle 
DEBUG = True

def main():
    questions = ['Who are the screenwriters for The Place Beyond The Pines?',
                'Who were the composers for Batman Begins?',
                'What awards did Frozen receive?',
                'How many awards did Frozen receive?',
                # 'How old is Jim Carrey?',
                # 'Which company distributed Avatar?',
                # 'Who is Leonardo diCaprio?',
                # "What is James Bond catchphrase?",
                # "Is Brad Pitt female?",
                # "Did Frozen win an award?",
                # "Did Frozen win any awards?",
                # 'Which company distributed Avatar?',
                # 'Who is the mommy of Leonardo diCaprio?',
                # "What is James Bond catchphrase?",
                # "Where did Brad Pitt go to school?",
                # "Who played Frodo Baggins?",
                # "Which movie was based on the book I Heard You Paint Houses (2004)?",
                #"Where did Brad Pitt go to school?",
                #'Which company distributed Avatar?',
                #'Who is Leonardo di Caprio?',
                #"What is James Bond catchphrase?",
                # "Where did Brad Pitt go to school?"
                "How many voice actors worked for Frozen?",
                # 'Which company distributed Avatar?',
                # 'Who is Leonardo di Caprio?',
                # "What is James Bond catchphrase?",
                # "Where did Brad Pitt go to school?",
                # 'Which company distributed Avatar?',
                # 'Who is Leonardo diCaprio?',
                # "What is James Bond catchphrase?",
                # "In what aspect ratio was Zack Snyder's Justice League shot?"
                "How long is Frozen?",
                "How long is Brad Pitt?"
                 ]

    links = readJson('property_links.json')
    for question in questions:
        print(question)
        answer = ask(question, links)
        print(f"Answer: {answer}")

def ask(question, links):
    parse = nlp(question)
    ent = getEnt(parse)
    print(ent)
    if len(ent) == 1:
        ent = ent[0]
        if parse[0].pos_ == 'AUX':
            return askYesNo(parse=parse,
                            ent=ent,
                            question=question,
                            links=links)

        if "how many" in question.lower() or "count" in question.lower():
            return askCount(parse=parse,
                            ent=ent,
                            question=question,
                            links=links)

        search_props = removeStopWords(question, ent)
        if (DEBUG):
            print("Search properties: " , search_props)
        ent_ids = getEntIds(ent)

        linked_props = getBestProp(search_props, links)
        if (DEBUG):
            print("Linked properties: " , linked_props)

        best_ent_id = getBestEntId(ent, ent_ids)

        if (DEBUG):
            print("entity ids: ", ent_ids)
        properties = getProperties(best_ent_id)

        #if (DEBUG):
        #   for p, v in properties.items():
        #       print(p, " : ", v)

        return findPropCombo(linked_props, properties)
    
    elif len(ent) == 2:
        search_props = removeStopWords2(question, ent)
        print("Search properties: ", search_props)
        for i in range(len(ent)):
            ent_ids = getEntIds(ent[i])
            linked_prop = getBestProp(search_props, links)
            if (DEBUG):
                print("Linked properties: ", linked_prop)

                print("entity ids: ", ent_ids)
            best_ent_id = getBestEntId(ent[i], ent_ids)

            properties = getProperties(best_ent_id)
    else:
        print('No entities found!')
        return []

def askCount(parse, ent, question, links):
    ''''
    Processes a question and counts the amount of results
    '''
    search_props = removeStopWords(question, ent)
    if (DEBUG):
        print("Search properties: " , search_props)
    
    ent_ids = getEntIds(ent)
    # Return 0 if no entities are found
    if len(ent_ids) == 0:
        return 0

    linked_props = getBestProp(search_props, links)
    if (DEBUG):
        print("Linked properties: " , linked_props)

    properties = getProperties(ent_ids[0])
    
    # Count results
    return len(findPropCombo(linked_props, properties))

def askYesNo(parse, ent, question, links):
    ''''
    Processes a question and checks if a property appears in the results
    '''
    search_props = removeStopWords(question, ent)
    if (DEBUG):
        print("Search properties: " , search_props)
    ent_ids = getEntIds(ent)

    linked_prop = getBestProp(search_props, links)
    if (DEBUG):
        print("Linked properties: " , linked_prop)

    # for token in parse:
    #     print(f"Lemma: {token.lemma_}")

    if len(ent_ids) == 0:
        return "No entities found"
    properties = getProperties(ent_ids[0])
    
    #for p, v in properties.items():
    #        print(p, " : ", v)
    
    print(f"Linkded prop: {properties[linked_prop]}")
    if parse[0] == 'Is':
        for prop in search_props:
            if properties[linked_prop][0] == prop:
                return "Yes"
            if prop in properties[linked_prop][0]:
                return "Yes"
        for token in parse:
            if token.pos_ == "ADJ":
                return "Yes"
    else:
        if properties[linked_prop][0]:
            return "Yes"
    return "No"

def getBestEntId(ent_name, ent_ids):
    '''
        Finds the entity found by sparql that has the lowest levenshtein distance
        from the original entity found.
    '''
    output = []
    i = 0
    for ent_id, found_ent in ent_ids:
        print(found_ent, ent_name)
        distance = lev(found_ent, ent_name)
        output.append((ent_id, found_ent, distance+i))
        i+=1
    
    if (DEBUG):
        print(output)
    return sorted(output, key = lambda x: x[2])[0]

def findPropCombo(linked_props, properties):
    '''
        Checks what the best property for the linked properties is.
        Will return the final answer.
    '''
    #Checks if there are no linked props left
    if len(linked_props) == 0:
        return []
    else:
        best_Linked_prop_index = max(linked_props.keys())
        best_Linked_prop = linked_props[best_Linked_prop_index]
        if best_Linked_prop in properties:
            return properties[best_Linked_prop]
        else:
            del linked_props[best_Linked_prop_index]
            return findPropCombo(linked_props, properties)

def execQuery(query, url):
    '''
        Executes a query given the url and query.
        @param query string containing the query.
        @param url a string with containing the url

        @return dictionary containing the request answer.
    '''
    req = requests.get(url, params={'query': query, 'format': 'json'})
    if req.status_code == 429:
        print('Too many requests, retrying....')
        time.sleep(5)
        return execQuery(query, url)
    if req.status_code == 200:
        results = req.json()
    else:
        print('Something went wrong, retrying...')
        time.sleep(5)
        return execQuery(query, url)

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
    if not parse.ents:
        for word in parse[1:]:
            if word.text.istitle() or word.text[0].isdigit():
                entity.append(int(word.i))
        if entity:
            return [' '.join(word.text for word in parse[entity[0]:(entity[-1]+1)])]
        else:
            return entity
    else:
        for ent in parse.ents:
            entity.append(ent.text)
    return entity


def removeStopWords(question, ent):
    '''
        Takes in a question in string form and return a list with spacy objects.
    '''
    question = question.replace(ent, '')
    no_stop_words = [word for word in nlp(question)
                     if (word.pos_ != 'PUNCT' # and not word.is_stop
                         and word != ' ') or word.i == 0]
    
    if (DEBUG):
        print(no_stop_words)

    return no_stop_words

def removeStopWords2(question, ent):
    for e in ent:
        question = question.replace(e, '')
    no_stop_words = [word for word in nlp(question)
                     if (word.pos_ != 'PUNCT' # and not word.is_stop
                     and word != ' ') or word.i == 0]

    if (DEBUG):
        print(no_stop_words)

    return no_stop_words


def getBestProp(search_props, links):
    same_prop_counts = {}
    for prop, related_props in links.items():
        
        same_props = [search_prop.lemma_.lower() for search_prop in search_props if search_prop.lemma_ in related_props]
        
        same_prop_amount = len(same_props)
        same_prop_counts[same_prop_amount] = prop

    if (DEBUG):
        print(same_prop_counts)
    max_key = max(same_prop_counts.keys())

    return same_prop_counts


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

    if (DEBUG):
        print(answer)

    prop, value = answer['head']['vars']

    output = {}
    for row in answer['results']['bindings']:
        if row[prop]['value'] in output:
            output[row[prop]['value']].append(row[value]['value'])
        else:
            output[row[prop]['value']] = [row[value]['value']]

    return output


def getPropertiesExtended(ent_id):
    '''
        Extended version on getProperties.
    '''
    url = 'https://query.wikidata.org/sparql'
    query = '''
                    SELECT ?wdLabel ?ps_Label ?wdpqLabel ?pq_Label {
                    VALUES (?company) {(wd:'''+ ent_id[0] +''')}

                    ?company ?p ?statement .
                    ?statement ?ps ?ps_ .

                    ?wd wikibase:claim ?p.
                    ?wd wikibase:statementProperty ?ps.

                    OPTIONAL {
                    ?statement ?pq ?pq_ .
                    ?wdpq wikibase:qualifier ?pq .
                    }

                    SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
                    } 
                    ORDER BY ?wd ?statement ?ps_
                    '''

    answer = execQuery(query, url)

    prop, value, prop_of_value, value_of_prop_of_value = answer['head']['vars']

    #print(answer['results']['bindings'])

    output = {}
    for row in answer['results']['bindings']:
        if row[prop]['value'] in output:
            output[row[prop]['value']].append(row[value]['value'])
        else:
            output[row[prop]['value']] = [row[value]['value']]

        if prop_of_value in row:
            if row[prop_of_value]['value'] in output:
                output[row[prop_of_value]['value']].append((row[value]['value'], row[value_of_prop_of_value]['value']))
            else:
                output[row[prop_of_value]['value']] = [(row[value]['value'], row[value_of_prop_of_value]['value'])]

    #print(output)

    return output


if __name__ == '__main__':
    main()