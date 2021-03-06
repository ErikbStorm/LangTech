import csv
import new_sparqlAsk

def main():
    #for x, y in new_sparqlAsk.getPropertiesExtended(['Q127367']).items():
    #    print(x, " : ", y)
    evalQuestions2('test_all1.csv', write=True)

def ask(question):
    pass

def evalQuestions(filename, write=True):
    output = []
    output2 = []
    links = new_sparqlAsk.readJson('property_links.json')
    with open(filename, 'r', encoding='UTF-8') as f:
        file = csv.reader(f, delimiter='\t')
        for i, row in enumerate(file):
            if i > 600 and i < 700:
                question = row[0]
                corr_answers = [answ.strip() for answ in row[2:]]

                print(question)
                try:
                    sys_answers = new_sparqlAsk.ask(question, links)
                except Exception as e:
                    #If program fails, then answer with No
                    print(e)
                    sys_answers = ['No']
                #print("Systeem antwoord: ", sys_answers)
                print(sys_answers, corr_answers)
                score = evaluate(sys_answers, corr_answers)
                print(score)
                output.append([i, score, sys_answers])
                output2.append([i, sys_answers])
            #if i > 20:
            #    break
    
    #Writing to a file.
    if write:
        write_file1 = open('scores_test.csv', 'w+', newline='')
        writer1 = csv.writer(write_file1, delimiter='\t')
        writer1.writerows(output)
        write_file1.close()

        write_file2 = open('answers_test.csv', 'w+', newline='')
        writer2 = csv.writer(write_file2, delimiter='\t')
        writer2.writerows(output)
        write_file1.close()

def evalQuestions2(filename, write=True):
    output = []
    output2 = []
    links = new_sparqlAsk.readJson('property_links.json')
    with open(filename, 'r', encoding='UTF-8') as f:
        file = csv.reader(f, delimiter='\t')
        for i, row in enumerate(file):
            question = row[1]
            corr_answers = [answ.strip() for answ in row[2:]]

            print(question)
            try:
                sys_answers = new_sparqlAsk.ask(question, links)
            except Exception as e:
                #If program fails, then answer with No
                print(e)
                sys_answers = ['No']
            print("Systeem antwoord: ", sys_answers)
            #print(sys_answers, corr_answers)
            #score = evaluate(sys_answers, corr_answers)
            #print(score)
            output.append([i, *sys_answers])
    
    #Writing to a file.
    if write:
        write_file1 = open('scores_test2.csv', 'w+', newline='')
        writer1 = csv.writer(write_file1, delimiter='\t')
        writer1.writerows(output)
        write_file1.close()


def evaluate(sys_answers, all_corr_answers):
    '''
        Returns the simple evaluation score.
        @param sys_answers a list containing all the answers.
        @param all_corr_answers a list containing all the correct answers

        @return A score indicating how good the answers are.
    '''
    try:
        if sys_answers != None:
            sys_answers = [answ.lower() for answ in sys_answers]
            all_corr_answers = [answ.lower() for answ in all_corr_answers]
            precision = getPrecision(sys_answers, all_corr_answers)
            recall = getRecall(sys_answers, all_corr_answers)
            if recall == 1 and precision == 1:
                return 1
            elif precision == 0.5:
                return 0.5
    except:
        return 0
    return 0


def getPrecision(sys_answers, all_corr_answers):
    '''
        Returns the precision based on the two lists.
        @param sys_answers a list containing all the answers.
        @param all_corr_answers a list containing all the correct answers

        @return a float that represents the precision
    '''
    corr_answers = [answ for answ in sys_answers if answ in all_corr_answers]
    return len(corr_answers) / float(len(sys_answers))

def getRecall(sys_answers, all_corr_answers):
    '''
        Returns the recall based on the two lists.
        @param sys_answers a list containing all the answers.
        @param all_corr_answers a list containing all the correct answers

        @return a float that represents the recall
    '''
    corr_answers = [answ for answ in sys_answers if answ in all_corr_answers]
    return len(corr_answers) / float(len(all_corr_answers))



if __name__ == '__main__':
    main()