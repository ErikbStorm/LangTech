import requests
import time
import json
import spacy
from Levenshtein import distance as lev

nlp = spacy.load("en_core_web_lg")
ruler = nlp.add_pipe("entity_ruler")
ruler.from_disk("patterns.jsonl")

# Global debug toggle
DEBUG = True

def main():
    questions = [#'Who are the screenwriters for The Place Beyond The Pines?',
                #'Who were the composers for Batman Begins?',
                #'What awards did Frozen receive?',
                #'How many awards did Frozen receive?',
                # 'How old is Jim Carrey?',
                # 'Which company distributed Avatar?',
                # 'Who is Leonardo diCaprio?',
                # "What is James Bond catchphrase?",
                #"Is Brad Pitt female?",
                #"Did Frozen win an award?",
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
                #"How many voice actors worked on Frozen?",
                # 'Which company distributed Avatar?',
                # 'Who is Leonardo di Caprio?',
                # "What is James Bond catchphrase?",
                # "Where did Brad Pitt go to school?",
                # 'Which company distributed Avatar?',
                # 'Who is Leonardo diCaprio?',
                # "What is James Bond catchphrase?",
                # "In what aspect ratio was Zack Snyder's Justice League shot?"
                #"How long is Frozen?",
                #"How long is Brad Pitt?",
                #"Where was The Avengers filmed?"
                #'Which locations were used to film the movie "Black Panther"(2018)'
                #"Who is the main character in Fifty Shades of Grey?",
                #"What is the sequel to Fifty Shades of Grey?",
                #"How many Twitter followers does Tom Hanks have?",
                #"How much did Frozen cost?",
                "What gender is Elliot Page?",
                "How many episodes does The Queen's Gambit have?"
                 ]

    links = readJson('property_links.json')
    for question in questions:
        print(question)
        answer = ask(question, links)
        print(f"Answer: {answer}")


def ask(question, links):
    '''
        Main function of the program, takes in a question and returns answer.
    '''
    parse = nlp(question)
    ent = getEnt(parse)
    if (DEBUG):
        print(ent)
    if len(ent) == 1:
        ent = ent[0]
        if parse[0].pos_ == 'AUX':
            return askYesNo(parse=parse,
                            ent=ent,
                            question=question,
                            links=links)

        splitted_question = question.lower().split()
        if "how many" in question.lower() or "how much" in question.lower() or "count" in splitted_question or "number" in splitted_question:
            return askCount(parse=parse,
                            ent=ent,
                            question=question,
                            links=links)

        #Retrieve the properties from the question.
        search_props = removeStopWords(question, ent)
        if (DEBUG):
            print("Only one entity detected!")
            print("Search properties: " , search_props)
        
        ent_ids = getEntIds(ent)
        if (DEBUG):
            print("Entity ids: ", ent_ids)

        #Link the propertires of the question to the linked properties.
        linked_props = getBestProp(search_props, links)
        if (DEBUG):
            print("Linked properties: " , linked_props)

        best_ent_id = getBestEntId(ent, ent_ids)
        ent_ids.remove(best_ent_id[:2])

        properties = getPropertiesExtended(best_ent_id)

        #First try to find answer with changing the properties
        answer = findPropCombo(linked_props.copy(), properties)

        #If still no answer, try the same properties for a different entity.
        return returnAnswer(linked_props, properties, ent_ids)
    
    #Execute this if there are 2 entities.
    elif len(ent) == 2:
        if parse[0].pos_ == 'AUX':
            return askYesNo(parse=parse,
                            ent=ent,
                            question=question,
                            links=links)

        search_props = removeStopWords2(question, ent)
        if (DEBUG):
            print("Two entities detected!")
            print("Search properties: ", search_props)
        answers = []
        for i in range(len(ent)):
            ent_ids = getEntIds(ent[i])
            linked_props = getBestProp(search_props, links)
            if (DEBUG):
                print("Linked properties: ", linked_props)

                print("entity ids: ", ent_ids)
            best_ent_id = getBestEntId(ent[i], ent_ids)

            properties = getPropertiesExtended(best_ent_id)
            ent2 = [x for x in ent if x != ent[i]][0]
            answer = findPropCombo2(linked_props, ent2, properties)
            if answer is not None:
                answers += answer
        if (DEBUG):
            print("Answers: ", answers)

        #If there are still no answers...

        if 'No' in answers or len(answers) == 0:
            ent = getEntBackup(parse)
            answers = []
            for i in range(len(ent)):
                if (DEBUG):
                    print("Only one entity detected!")
                    print("Search properties: " , search_props)
                ent_ids = getEntIds(ent[i])

                linked_props = getBestProp(search_props, links)
                if (DEBUG):
                    print("Linked properties: " , linked_props)

                best_ent_id = getBestEntId(ent[i], ent_ids)
                ent_ids.remove(best_ent_id[:2])

                if (DEBUG):
                    print("entity ids: ", ent_ids)
                properties = getProperties(best_ent_id)


                answer = findPropCombo(linked_props.copy(), properties)
                if answer == ['No']:
                    properties = getProperties(ent_ids[0])
                    answer = findPropCombo(linked_props, properties)
                
                #only add answer if it is meaningful.
                if answer != ['No']:
                    answers += answer
        if len(answers) == 0:
            answers = ['No']
        return answers
    
    #Execute this if there are 3 entities.
    elif len(ent) == 3:
        if (DEBUG):
            print("Three entities detected!")
        search_props = removeStopWords2(question, ent)
        answers = []
        ents21 = ent[0] + ' ' + ent[1]
        ents22 = ent[1] + ' ' + ent[2]
        ents23 = ent[0] + ' ' + ent[2]
        for i in range(len(ents21)):
            ent_ids = getEntIds(ents21[i])
            linked_props = getBestProp(search_props, links)
            if (DEBUG):
                print("Linked properties: ", linked_props)

                print("entity ids: ", ent_ids)
            best_ent_id = getBestEntId(ents21[i], ent_ids)

            properties = getPropertiesExtended(best_ent_id)
            ent2 = [x for x in ents21 if x != ent[i]][0]
            answers.append(findPropCombo2(linked_props, ent2, properties))
        for i in range(len(ents22)):
            ent_ids = getEntIds(ents22[i])
            linked_props = getBestProp(search_props, links)
            if (DEBUG):
                print("Linked properties: ", linked_props)

                print("entity ids: ", ent_ids)
            best_ent_id = getBestEntId(ents22[i], ent_ids)

            properties = getPropertiesExtended(best_ent_id)
            ent2 = [x for x in ents22 if x != ent[i]][0]
            answers.append(findPropCombo2(linked_props, ent2, properties))
        for i in range(len(ents23)):
            ent_ids = getEntIds(ents23[i])
            linked_props = getBestProp(search_props, links)
            if (DEBUG):
                print("Linked properties: ", linked_props)

                print("entity ids: ", ent_ids)
            best_ent_id = getBestEntId(ents23[i], ent_ids)

            properties = getPropertiesExtended(best_ent_id)
            ent2 = [x for x in ents23 if x != ent[i]][0]
            answers.append(findPropCombo2(linked_props, ent2, properties))
        return answers
    else:
        return ['No']


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
        return ["0"]

    linked_props = getBestProp(search_props, links)
    if (DEBUG):
        print("Linked properties: " , linked_props)

    properties = getProperties(ent_ids[0])

    #check if results contains a number
    search_list = [term.text for term in search_props]

    result = returnAnswer(linked_props, properties, ent_ids)
    if len(result) == 1 and result[0].isdigit():
        return(str(result))
    else:
        # Count results
        return [str(len(result))]


def askYesNo(parse, ent, question, links):
    ''''
    Processes a question and checks if a property appears in the results
    '''
    search_props = removeStopWords(question, ent)
    if (DEBUG):
        print("Search properties: " , search_props)
    ent_ids = getEntIds(ent)

    linked_props = getBestProp(search_props, links)
    if (DEBUG):
        print("Linked properties: " , linked_props)

    if len(ent_ids) == 0:
        return "No entities found"
    properties = getProperties(ent_ids[0])

    prop_combo = findPropCombo(linked_props, properties)
    if (DEBUG):
        print("Prop combo: " , prop_combo)

    if parse[0].text == 'Is':
        for key, prop in linked_props:
            if prop in properties:
                search_list = [term.lemma_ for term in search_props]
                if any(term in search_list for term in properties[prop]):
                    return ["Yes"]
                
        # for token in parse:
        #     if token.pos_ == "ADJ":
        #         return "Yes"
    elif len(linked_props) > 0:
            return ["Yes"]
            
    return ["No"]


def askYesNo2(parse, ent, question, links):
    ''''
    Processes a question and checks if a property appears in the results
    '''
    search_props = removeStopWords2(question, ent)

    answers = []
    for i in range(len(ent)):
        ent_ids = getEntIds(ent[i])
        linked_props = getBestProp(search_props, links)
        if (DEBUG):
            print("Linked properties: ", linked_props)

            print("entity ids: ", ent_ids)
        best_ent_id = getBestEntId(ent[i], ent_ids)

        properties = getPropertiesExtended(best_ent_id)
        ent2 = [x for x in ent if x != ent[i]][0]
        answers.append(findPropCombo2(linked_props, ent2, properties))

        if parse[0].text == 'Is':
            for prop in linked_props:
                if prop in properties:
                    search_list = [term.lemma_ for term in search_props]
                    if any(term in search_list for term in properties[prop]):
                        return ["Yes"]

        # for token in parse:
        #     if token.pos_ == "ADJ":
        #         return "Yes"
        elif len(linked_props) > 1:
            return ["Yes"]
    return ["No"]


def returnAnswer(linked_props, properties, ent_ids):
    '''
        Tries 2 different entities, to get a satisfatory answer.
    ''' 
    answer = findPropCombo(linked_props.copy(), properties)
    if answer == ['No']:
        properties = getProperties(ent_ids[0])
        answer = findPropCombo(linked_props, properties)
    return answer

def getBestEntId(ent_name, ent_ids):
    '''
        Finds the entity found by sparql that has the lowest levenshtein distance
        from the original entity found.
    '''
    output = []
    i = 0
    for ent_id, found_ent in ent_ids:
        #print(found_ent, ent_name)
        distance = lev(found_ent, ent_name)
        output.append((ent_id, found_ent, distance+i))
        i+=1

    if (DEBUG):
        print(output)
    try:
        return sorted(output, key = lambda x: x[2])[0]
    except:
        print("No entities found!")


def findPropCombo(linked_props, properties, search_props=None):
    '''
        Checks what the best property for the linked properties is.
        Will return the final answer.
    '''
    #Checks if there are no linked props left
    if len(linked_props) == 0:
        return ['No']
    else:
        best_Linked_prop = linked_props[0][1]
        #print(best_Linked_prop)
        if best_Linked_prop in properties:
            print("Antwoordx ", properties[best_Linked_prop])

            #If it is a list then execute this.
            
            if type(properties[best_Linked_prop][0]) == dict:
                return [dict['val'] for dict in properties[best_Linked_prop]]

            else:
                return properties[best_Linked_prop]
        else:
            del linked_props[0]
            return findPropCombo(linked_props, properties)


def findPropCombo2(linked_props, entity2, properties):
    '''
        Checks what the best property for the linked properties is.
        Will return the final answer. Used when having more entities.
    '''
    #Checks if there are no linked props left
    if len(linked_props) == 0:
        return ['No']
    else:
        best_Linked_prop = linked_props[0][1]
        if best_Linked_prop in properties:
            for tuple in properties[best_Linked_prop]:
                if tuple[1] == entity2:
                    return tuple[0]
                elif tuple[0] == entity2:
                    return tuple[1]
        else:
            del linked_props[0]
            return findPropCombo2(linked_props, entity2, properties)

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
    if len(parse.ents) == 0:
        for word in parse[1:]:
            if word.text.istitle() or word.text[0].isdigit():
                entity.append(int(word.i))
        if entity:
            return [' '.join(word.text for word in parse[entity[0]:(entity[-1]+1)])]
        else:
            return entity
    else:
        for ent in parse.ents:
            if ent.text == 'first':
                continue
            entity.append(ent.text)
    return entity

def getEntBackup(parse):
    entity = list()
    for word in parse[1:]:
        if word.text.istitle() or word.text[0].isdigit():
            entity.append(int(word.i))
    if entity:
        return [
            ' '.join(word.text for word in parse[entity[0]:(entity[-1] + 1)])]
    else:
        return entity

def removeStopWords(question, ent):
    '''
        Takes in a question in string form and return a list with spacy objects.
    '''
    question = question.replace(ent, '')
    no_stop_words = [word for word in nlp(question)
                     if (word.pos_ != 'PUNCT' # and not word.is_stop
                         and word.text != ' ') or word.i == 0]

    if (DEBUG):
        print(no_stop_words)

    return no_stop_words


def removeStopWords2(question, ent):
    for e in ent:
        question = question.replace(e, '')
    no_stop_words = [word for word in nlp(question)
                     if (word.pos_ != 'PUNCT' # and not word.is_stop
                     and word.text != ' ') or word.i == 0]

    if (DEBUG):
        print(no_stop_words)

    return no_stop_words


def getBestProp(search_props, links, stop_word_weight=0.1):
    '''
        Returns the best linked properties based on the linked property list.
    '''
    same_prop_counts = []
    for prop, related_props in links.items():
        #List with overlapping props
        same_props = [search_prop for search_prop in search_props if search_prop.lemma_ in related_props]

        #list of same props without the stop words
        same_lemma_props_without_stop_words = [prop.lemma_.lower() for prop in same_props if not prop.is_stop]

        #list with only stop words
        same_prop_stop_words = [prop.lemma_.lower() for prop in same_props if prop.is_stop]

        #Same prop amount with stop word weight.
        same_prop_amount = len(same_lemma_props_without_stop_words) + (stop_word_weight * float(len(same_prop_stop_words)))

        same_prop_counts.append((same_prop_amount, prop))


    sorted_counts = sorted(same_prop_counts, key = lambda x: x[0], reverse=True)

    return [(c,prop) for c, prop in sorted_counts if c != 0][:4]


def getAnswer(search_pred, properties):
    distances = {}
    for property, values in properties.items():
        distance = lev(property, search_pred)
        distances[distance] = (property, values)

    id_with_lowest_distance = min(distances.keys())

    return distances[id_with_lowest_distance]


def getProperties(ent_id):
    if (DEBUG):
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

    #print(answer)

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
        r_prop = row[prop]['value']
        r_val = row[value]['value']

        if r_prop in output:
            output[r_prop].append(r_val)
        else:
            output[r_prop] = [r_val]

        #Inserting the properties of the values.
        if prop_of_value in row:
            r_prop_of_value = row[prop_of_value]['value']
            r_val_value = row[value_of_prop_of_value]['value']
            if r_prop_of_value in output:
                output[r_prop_of_value].append({r_prop : r_val, "val" : r_val_value})
            else:
                output[r_prop_of_value] = [{r_prop : r_val, "val" : r_val_value}]

    #print(output)

    return output


if __name__ == '__main__':
    main()