import pickle
import requests
import re


def main():
    pattern_list = list()
    url = 'https://query.wikidata.org/sparql'
    query = "SELECT ?workLabel WHERE { ?work wdt:P31 wd:Q11424. SERVICE wikibase:label { bd:serviceParam wikibase:language 'en'. }}"
    results = requests.get(url, params={'query': query, 'format': 'json'}).json()
    for result in results['results']['bindings']:
        if re.match(r"^Q[0-9]+", result['workLabel']['value']):
            continue
        pattern_list.append({"label": "MOVIE", "pattern": result['workLabel']['value']})
    print(pattern_list)
    with open('patterns.pickle', 'wb') as f:
        pickle.dump(pattern_list, f)


if __name__ == "__main__":
    main()
