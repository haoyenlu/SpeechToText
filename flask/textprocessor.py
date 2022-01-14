#TODO
import functools
import subprocess
import re
import nltk
from nltk.tokenize import word_tokenize
import xml.etree.ElementTree as ET


class TextProcessor:
    
    @staticmethod
    def pos_tag_to_words(sentence):
        words =  word_tokenize(sentence)
        tag_words = nltk.pos_tag(words)

        return tag_words

    @staticmethod
    def write_pattern_to_file(sentence) -> bool:
        tag_words = pos_tag_to_words(sentence)
        tag_list = [word[1] for word in tag_words] 

        string = ''.join(x.ljust(5) for x in tag_list)

        append = not find_pattern(tag_list) # don't append if find the pattern 
        
        if append:
            with open("analyze_text.txt","a") as text_file:
                text_file.write(string)
                text_file.write("\n")

        return append

    @staticmethod
    def find_pattern(pattern_to_search:list) -> bool:
        """enter the pattern , return true if find the pattern in the text file."""
        find = False
        with open("analyze_text.txt","r") as text_file:
            for line in text_file:
                pattern_list = re.split(r' *',line)[:-1]
                if len(pattern_list) == len(pattern_to_search):
                    if functools.reduce(lambda x , y : x and y , map(lambda p , q : p == q,pattern_list,pattern_to_search), True):
                        find = True

        return find

    @staticmethod
    def add_punctuation(sentence) -> str:
        if type(sentence) is not str:
            return sentence
        
        if sentence.find('.') >= 0 or sentence.find('?') >= 0:
            return sentence

        sent_list = sentence.split(' ')
        question = ["who","where","why","how","what","when","can","do","did"]
        if sent_list[0].lower() in question:
            sentence += '?'
        else:
            sentence += '.'

        return sentence

    @staticmethod
    def parser(sentence):
        tag_words  = TextProcessor.pos_tag_to_words(sentence)

        chunk_grammar = """P:{<PRP$>|<NNP><POS>}            # Possesive
                        NP:{<IN>?<JJS>?<DT>?<CD>*<JJ.*>*<NN.*>}
                        NP_P:{<P.*>|(<P>?<NP>)}
                        VP:{(<VB.><RB>)?<V.*><RB>?<NP_P>}   # Verb phrase
                        AP:{<VB.><JJ>}                      # Adjective phrase
                        SP:{<NP_P>(<CC><NP_P>)?(<VP>|<AP>)} # Simple phrase
                        QP:{<W.*><VP>}                      # Question phrase
                        find:{<SP>((<CC>|<RB>)(<SP>|<NP_P>|<VP>|<AP>))*}
                        find_2:{<QP>}"""
        chunk_parser = nltk.RegexpParser(chunk_grammar)
        chunk_data = chunk_parser.parse(tag_words)
        
        #print(chunk_data)
            
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

        
                
    @staticmethod
    def grammar_check(sentence):
        load_grammar = nltk.data.load('file:english_grammar.cfg')
        wrong_syntax = True
        sent_split = nltk.word_tokenize(sentence.lower())
        rd_parser = nltk.RecursiveDescentParser(load_grammar)
        tree_list =  rd_parser.parse(sent_split)
        for tree in tree_list:
            wrong_syntax = False
            #print(tree)
            #print("Correct Grammar !!!")

        
        return not wrong_syntax

        
    @staticmethod
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
    example = "every man is a human."
    tp = TextProcessor
    #print(tp.ace_parsing(example , "-csyntax" , "-cparaphrase" , "-cdrs"))


