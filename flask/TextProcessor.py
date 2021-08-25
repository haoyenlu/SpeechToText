#TODO
import subprocess
import re
import string 
import numpy as np
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import gutenberg
import xml.etree.ElementTree as ET

from timer import Timer


def add_punctuation(sentence):
    """giving a sentence without punctuation , return a sentence with punctuation"""
    words =  word_tokenize(sentence)
    tag_words = nltk.pos_tag(words)

    chunk_grammar = """NP:{<IN>?<JJS>?<DT>?<CD>*<JJ.*>*<NN.*>}
                    NP_P:{<NP>|<P.*>}
                    VP:{(<VB.><RB>)?<V.*><RB>?<NP_P>}   # Verb phrase
                    AP:{<VB.><JJ>}                      # Adjective phrase
                    SP:{<NP_P>(<CC><NP_P>)?(<VP>|<AP>)} # Simple phrase
                    QP:{<W.*><VP>}                      # Question phrase
                    find:{<SP>((<CC>|<RB>)(<SP>|<NP_P>|<VP>|<AP>))*}
                    find_2:{<QP>}"""
    chunk_parser = nltk.RegexpParser(chunk_grammar)
    chunk_data = chunk_parser.parse(tag_words)
    
    print(chunk_data)
        
    correct_sent_list = []
    for child in chunk_data.subtrees(lambda t:t.label() == 'find'):
        child.append('.')
        for item in child.leaves():
            correct_sent_list.append(item[0])

    for child in chunk_data.subtrees(lambda t:t.label() == 'find_2'):
        child.append('?')
        for item in child.leaves():
            correct_sent_list.append(item[0])

    if len(correct_sent_list) is 0:
        raise Exception('Textproccessor cannot parse the sentence.')

    return " ".join(correct_sent_list)

    
            

def grammar_check(sentence):
    load_grammar = nltk.data.load('file:english_grammar.cfg')
    wrong_syntax = True
    sent_split = nltk.word_tokenize(sentence.lower())
    rd_parser = nltk.RecursiveDescentParser(load_grammar)
    tree_list =  rd_parser.parse(sent_split)
    for tree in tree_list:
        wrong_syntax = False
        print(tree)
        print("Correct Grammar !!!")

    if wrong_syntax :
        print("Wrong Grammar !!!")
    
    return not wrong_syntax

    

def ace_parsing(text,*args):
    command = ["../APE/ape.exe","-text",text]
    for arg in args:
        command.append(arg)
    
    proc = subprocess.run(args = command,universal_newlines = True,stdout = subprocess.PIPE,stderr = subprocess.PIPE)
    stdout , stderr = proc.stdout , proc.stderr
    if stdout is not "":
        root = ET.fromstring(stdout)
        result = dict()
        for child in root:
            result[child.tag] = child.text
        messages = root.find('messages')
        for child in messages:
            result['messages'] = child.attrib

        return result
                
    else :
        raise Exception(stderr)




if __name__ == '__main__':
    example_quote = """Every person is Alex or is Bob or is Carlo"""
    #TextProcessor.grammar_check(example_quote)
    correct_sent = add_punctuation(example_quote)
    print(correct_sent)
    #ace_result = TextProcessor.ace_parsing(example_quote,"-cdrspp","-cdrsxml")
    #print(ace_result)
    #correct_sent = TextProcessor.add_punctuation(example_quote)
    #print(correct_sent)


