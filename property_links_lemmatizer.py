import json
import spacy

nlp = spacy.load("en_core_web_trf")

def readJson(filename):
    with open(filename, 'r') as f:
        json_dict = json.load(f)
    return json_dict


def dumpJson(filename, dic):
    with open(filename, 'w') as f:
        json.dump(dic, f, indent=4)


def lemmaPropLinks(json_dict):
    for prop, links in json_dict.items():
        new_links = []
        for link in links:
            for token in nlp(link):
                new_links.append(token.lemma_)
        json_dict[prop] = new_links
    return json_dict

def main():
    json = readJson('property_links.json')
    dumpJson("property_links_org.json", json)
    new_dict = lemmaPropLinks(json)
    dumpJson("property_links_lemma.json", new_dict)
    

if __name__ == '__main__':
    main()