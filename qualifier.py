import spacy
import requests


def main():
    nlp = spacy.load('en_core_web_md')
    nlp.add_pipe('entityLinker', last=True)
    #question = input('Please ask a question:\n')
    parse = nlp("What movie won best picture in the 2020 Academy Awards?")
    for sent in parse.sents:
        sent._.linkedEntities.pretty_print()
    #entities = parse._.linkedEntities.pretty_print()
    verb_dict = {'play': ('actor', 'role'), 'won': ('award', 'winner'), 'release': ('release date', 'publication place')}
    if len(entities) == 2:
        for word in parse:
            if word.dep_ == 'root' and word.lemma_ in verb_dict:
                prop = verb_dict[word.lemma_]
    # Get property uri
    url = 'https://www.wikidata.org/w/api.php'
    params = {'action': 'wbsearchentities',
              'language': 'en',
              'format': 'json',
              'type': 'property'}
    prop_ids = list()
    for p in prop:
        params['search'] = p
        json = requests.get(url, params).json()
        if json['search']:
            prop_ids.append(json['search'][0]['id'])
        else:
            return 'No answer found'

    # create SPARQL query for each key-word
    answers = list()
    entity1 = 'Q' + entities[0]
    entity2 = 'Q' + entities[1]
    query = "SELECT ?answerLabel WHERE { wd:" + entity2 + " p:" + prop_ids[0] \
            + " [ ps:" + prop_ids[0] + " ?answer; pq:" + prop_ids[1] + "wd:" + entity1 \
            + "]. SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' }}"
    url = 'https://query.wikidata.org/sparql'
    results = requests.get(url, params={'query': query,
                                        'format': 'json'}).json()
    if results['results']['bindings']:
        for result in results['results']['bindings']:
            answers.append(result['answerLabel']['value'])
    return '\n'.join(set(answers))


if __name__ == '__main__':
    main()