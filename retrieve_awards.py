import pickle
import requests
import re


def main():
    pattern_list = list()
    url = 'https://query.wikidata.org/sparql'
    query = """SELECT DISTINCT ?awardLabel 
WHERE
{
  ?award wdt:P31 wd:Q16913666.
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en'. }
}"""
    results = requests.get(url, params={'query': query, 'format': 'json'}).json()
    for result in results['results']['bindings']:
        if re.match(r"^Q[0-9]+", result['awardLabel']['value']):
            continue
        pattern_list.append({"label": "AWARD", "pattern": result['awardLabel']['value']})
    pattern_list.append({"label": "AWARD", "pattern": "Academy Awards"})
    pattern_list.append({"label": "AWARD", "pattern": "Oscars"})
    pattern_list.append({"label": "AWARD", "pattern": "Oscar"})
    print(pattern_list)
    with open('awards.pickle', 'wb') as f:
        pickle.dump(pattern_list, f)


if __name__ == "__main__":
    main()