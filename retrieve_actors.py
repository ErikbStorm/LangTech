import pickle
import requests
import re


def main():
    pattern_list = list()
    url = 'https://query.wikidata.org/sparql'
    query = """SELECT DISTINCT ?actorLabel 
WHERE
{
  ?actor wdt:P106 wd:Q10800557.
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en'. }
}"""
    results = requests.get(url, params={'query': query, 'format': 'json'}).json()
    for result in results['results']['bindings']:
        if re.match(r"^Q[0-9]+", result['actorLabel']['value']):
            continue
        pattern_list.append({"label": "ACTOR", "pattern": result['actorLabel']['value']})
    print(pattern_list)
    with open('actors.pickle', 'wb') as f:
        pickle.dump(pattern_list, f)


if __name__ == "__main__":
    main()