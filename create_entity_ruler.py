import pickle
import spacy


def main():
    nlp = spacy.load("en_core_web_sm")
    ruler = nlp.add_pipe("entity_ruler")
    pickles = ['movies.pickle', 'actors.pickle', 'awards.pickle']
    for p in pickles:
        with open(p, 'rb') as f:
            pattern = pickle.load(f)
            ruler.add_patterns(pattern)
    ruler.to_disk("patterns.jsonl")


if __name__ == "__main__":
    main()