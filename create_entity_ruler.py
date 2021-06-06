import spacy
import requests
import re


def retrieve_patterns(query, ruler, label):
    print(f"Retrieving %s labels..." % label)
    url = 'https://query.wikidata.org/sparql'
    results = requests.get(url,
                           params={'query': query, 'format': 'json'}).json()
    print(f"Adding %s labels to Ruler..." % label)
    for result in results['results']['bindings']:
        if re.match(r"^Q[0-9]+", result['itemLabel']['value']):
            continue
        ruler.add_patterns([{"label": label, "pattern": result['itemLabel']['value']}])
    return ruler


def main():
    nlp = spacy.load("en_core_web_trf")
    ruler = nlp.add_pipe("entity_ruler")
    retrieve_patterns("""SELECT DISTINCT ?itemLabel 
WHERE
{ 
  ?item (wdt:P166|wdt:P1411) ?award;
         wdt:P31 wd:Q11424.
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en'. }
}""", ruler, "MOVIE")
    retrieve_patterns("""SELECT DISTINCT ?itemLabel 
WHERE
{ 
  ?item (wdt:P166|wdt:P1411) ?award;
         wdt:P106 wd:Q10800557.
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en'. }
}""", ruler, "ACTOR")
    retrieve_patterns("""SELECT DISTINCT ?itemLabel 
WHERE
{
  ?item wdt:P31 wd:Q16913666.
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en'. }
}""", ruler, "AWARD")
    ruler.to_disk("patterns.jsonl")


if __name__ == "__main__":
    main()
