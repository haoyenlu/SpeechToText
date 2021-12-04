import os
import re
import subprocess
import requests

JAVA_PATH = './jdk-16.0.2/bin/'
url = 'http://corenlp.run/'

SENTENCES = {'ROOT', 'S', 'SBARQ', 'SQ', 'SBAR', 'SINV'}
PHRASES = {
    'ADJP', 'ADVP', 'CONJP', 'FRAG', 'INTJ', 'LST', 'NAC', 'NP', 'NX', 'PP',
    'PRN', 'PRT', 'QP', 'RRC', 'UCP', 'VP', 'WHADJP', 'WHADVP', 'WHNP', 'WHPP',
    'NML',
}
MODIFIERS = {'JJ', 'JJS', 'JJR', }
DT_CD = {'DT', 'CD', 'HYPH', 'POS', 'WDT'}
EXCEPTIONS = {'everything', 'something', 'everyone', 'someome', 'nothing', 'thing'}


def fix_sent(input: str):
    # run stanford nlp by sebprocess, abandoned
    """
    cmd = [
        JAVA_PATH + 'java',
        '-mx2g',
        '-cp',
        'stanford-corenlp-4.2.2/*',
        'edu.stanford.nlp.pipeline.StanfordCoreNLP',
        '-annotators',
        'tokenize,ssplit,truecase,pos',#,lemma,ner',
        '-outputFormat',
        'conll',
        '-file',
        input,
        '-truecase.bias',
        'INIT_UPPER:0,LOWER:20,UPPER:0,O:0',
        '-truecase.overwriteText',
        #'-truecase.verbose'
    ]
    result = subprocess.run(cmd, capture_output = True)
    """
    # post request to stanford nlp server
    with open(input, mode='r') as file:
        data = file.read()
    conll = requests.post(url + '?properties={"annotators":"tokenize,ssplit,truecase,pos,lemma,ner","outputFormat":"conll","truecase.bias":"INIT_UPPER:0,LOWER:20,UPPER:0,O:0","truecase.overwriteText":"true"}', data= data).text

    #print(conll)
    truecase = ''
    pset = set()
    # read output
    sents = conll.split(os.linesep + os.linesep)
    if '' == sents[-1]:
        sents = sents[:-1]
    for i in range(len(sents)):
        sents[i] = sents[i].split(os.linesep)
        for j in range(len(sents[i])):
            sents[i][j] = sents[i][j].split('\t')
    #for sent in sents:
    #    print('------')
    #    print(sent)

    # compose sentences
    for i in range(len(sents)):
        for j in range(len(sents[i])):
            # get label
            label = sents[i][j][3]
            if label.__contains__('-'):
                label = label[:label.index('-')]
            
            # fix
            token = sents[i][j][1]
            if sents[i][j][2][0].islower():
                token = sents[i][j][1].lower()
            if 'NN' == label and sents[i][j][1].lower() not in EXCEPTIONS:
                #print(sents[i][j])
                pos = j - 1
                fix = True
                # check if is pronoun
                if  sents[i][j][1][0].isupper():
                    if len(sents[i][j][1]) == 1 or (len(sents[i][j][1]) > 1 and sents[i][j][1][1:].isnumeric()):
                        token = token.upper()
                        fix = False
                        pos = -1
                
                # fix
                while pos > -1:
                    if sents[i][pos][3] in MODIFIERS:
                        #print(sents[i][pos])
                        pos = pos - 1
                    elif sents[i][pos][3] in DT_CD:
                        fix = False
                        break
                    else:
                        break
                if fix:
                    if token not in pset:
                        pset.add(token)
                    truecase = truecase + 'p:' + token + ' '
                else: truecase = truecase + token + ' '

            else:
                if sents[i][j][3] != 'NNP' and token in pset:
                    truecase = truecase + 'p:'
                truecase = truecase + token + ' '
        truecase = truecase + '\n'

    # post process
    if truecase.__contains__('-'):
        truecase = re.sub('\s*-\s*', '-', truecase)
    if truecase.__contains__('-p:'):
        truecase = truecase.replace('-p:', '-')
    if truecase.__contains__(' n\'t ' ):
        truecase = truecase.replace(' n\'t ', ' not ')

    return truecase




