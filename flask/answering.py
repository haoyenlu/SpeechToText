import os
import subprocess
import string

APE_PATH = '../APE/ape.exe'

class Syntax_Tree:
    def __init__(self, token_data):
        self.token_data = token_data
        self.current_dict = {}
        self.data = []
        self.parse()
    def parse(self):
        if(self.isdict()):  # dict
            self.token_data=self.token_data.split(',', 1)
            name = self.token_data[0][1:]
            data_list = self.token_data[1][:-1]+';'
            # if(name == 'var'):
            #     return
            self.current_dict[name] = Syntax_Tree(data_list).data
        else:               # data list
            if(self.token_data.find(',') == -1):
                if(self.token_data in string.punctuation):
                    self.current_dict['punct'] = self.token_data
                else:
                    self.data = self.token_data[:-1].strip("\'")
                    self.current_dict['_'] = self.token_data.strip("\'")
                return
            begin = 0
            l = len(self.token_data)
            c = 0
            stack = []
            for i in range(l):
                if(self.token_data[i] == '['):
                    c += 1
                elif(self.token_data[i] == ']'):
                    c -= 1
                elif(self.token_data[i] == ',' and c == 0):
                    stack.append(Syntax_Tree(self.token_data[begin:i]).current_dict)
                    begin = i+1
                elif(self.token_data[i] == ';'):
                    stack.append(Syntax_Tree(self.token_data[begin:i]).current_dict)
            self.data = stack
    def isdict(self):
        return (self.token_data[0] == '[' and self.token_data[-1] == ']')
    def traverse(self, node):
        ans = ""
        if(type(node) == type(list())):
            for child in node:
                ans += self.traverse(child)
        elif(type(node) == type(dict())):
            for key in node:
                if(key == 'punct'):
                    # print(node[key])
                    ans += str(node[key])+'\n'
                elif(key == 'var'):
                    pass
                else:
                    ans += self.traverse(node[key])
        elif(type(node) == type(str())):
            # print(node, end = ' ')
            ans += node +' '
        return ans
    def syntaxList(self):
        if('root' in self.current_dict):
            return self.current_dict['root']
        else:
            return []
        # for i, s in enumerate(self.current_dict['tree']):
            #     print("sentence: "+str(i))
            #     print(s['specification'], end = "\n\n")

def _find(s: dict, nodetype: str):
    for key in s:
        if(key == nodetype):
            return s
        for child in s[key]:
            if(type(child) != type(dict())):
                continue
            if _find(child, nodetype) is not None:
                return _find(child, nodetype)
    return None

def answer(question: str, ans: tuple):
    no_exception = True
    exception_content = None
    if not os.path.isfile(APE_PATH):
        no_exception = False
        exception_content = "APE path error"
        return None, no_exception, exception_content

    status, s_output = subprocess.getstatusoutput(APE_PATH + ' -text "' + question + '" -solo paraphrase -guess')
    if(s_output.find("importance=\"error\"") != -1):
        # TODO: add specification to error from s_output
        # error s_output example: 
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # <messages>                                                    #
        #     <message                                                  #
        #         importance="error"                                    #
        #         type="sentence"                                       #
        #         sentence=""                                           #
        #         token=""                                              #
        #         value="crime"                                         #
        #         repair="Every ACE text must end with . or ? or !."/>  #
        # </messages>                                                   #
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        no_exception = False
        exception_content = "sentence errer"
        return None, no_exception, exception_content


    sentence = s_output.replace('\n', ' ')
    _, syntax = subprocess.getstatusoutput(APE_PATH + ' -text "' + sentence + '" -solo syntax -guess')

    #print("syntax:", syntax)
    
    tree = Syntax_Tree("[root," + syntax[1:])
    
    question = None
    for s in tree.current_dict['root']:
        if(_find(s, "query") != None):
            question = s
            break

    # replace qpn with answer
    # syntax example:           
    # # # # # # # # # # # # # # #
    #              query        #
    #     _________|_________   #
    #     question          |   #
    # ____|_____            |   #
    # np       vp           |   #
    # |        |            |   #
    # qpn      vbar         |   #
    # |        |            |   #
    # |        vcompl       |   #
    # |   _____|_____       |   #
    # |   v         np      |   #
    # |   |       __|__     |   #
    # |   |       det nbar  |   #
    # |   |       |   |     |   #
    # |   |       |   n     |   #
    # |   |       |   |     |   #
    # who commits a   crime ?   #
    # # # # # # # # # # # # # # #
    if(question == None):
        no_exception = False
        exception_content = "sentence error: sentence is not a question"
        return None, no_exception, exception_content
    #print(tree.traverse(question))
    if(_find(question, "punct") != None):
        _find(question, "punct")['punct'] = '.'
    if(type(ans) != type(tuple())):
        no_exception = False
        exception_content = "type of 'ans' should be tuple"
        return None, no_exception, exception_content
    if(len(ans) == 0):
        no_exception = False
        exception_content = "tuple lenth should not be 0"
        return None, no_exception, exception_content
    if(_find(question, "qpn") != None):
        if(len(ans[0]) != 0):   #tuple第一種答案 (人名)
            _find(question, "qpn")['qpn'] = ans[0][0]
        # TODO: 第二種答案和第三種答案
        elif(len(ans[1]) != 0): #tuple第二種答案 (class)
            for x in ans[1]:
                if ():
                    className = x
            _find(question, "qpn")['qpn'] = 'Every ' + className
        # elif(len(ans[2]) != 0): #tuple第三種答案 (infered class)
        #     pass
        else: #空集合??                  
            if(_find(question, "qpn")['qpn'].lower() == 'who'):
                _find(question, "qpn")['qpn'] = 'Nobody'
            else:
                _find(question, "qpn")['qpn'] = 'Nothing'
    
            
    elif(_find(question, "qdet") != None):
        _find(question, "qdet")['qdet'] = ans
    else:
        no_exception = False
        exception_content = "sentence error: cannot find qpn or qdet"
        return None, no_exception, exception_content
    

    response = tree.traverse(question)
    no_exception = True
    exception_content = None
    return response, no_exception, exception_content

if __name__ == "__main__":
    #how to use
    query = str(input())
    ans = (tuple(["ANSWER"]),(),()) # tuple
    response = answer(query, ans)

    print(response)