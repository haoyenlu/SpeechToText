from solver import *
import fixSent
import datetime
from nltk import sent_tokenize

def getAnswer(fname):
    fix = sent_tokenize(fixSent.fix_sent(fname))
    puzzle = fix[:-1]
    question = fix[-1]

    name = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
    with open(name, 'w') as file:
        file.write('\n'.join(puzzle))
    with open(name + '_q', 'w') as file:
        file.write(question)

    rtn = False
    result = None
    try:
        result = solver.solve(name, name + '_q')
    except Exception as e:
        #print(str(e))
        question = None
    else:
        if result == None:
            #print(solver.lasterror)
            question = None
        else:
            rtn = True
    finally:
        os.remove(name)
        os.remove(name + '_q')
    return (rtn, result, question)

#print(getAnswer('testinput.txt'))
