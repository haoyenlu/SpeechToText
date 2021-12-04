import os
import sys
import errno
import re
import subprocess
import concurrent.futures
import datetime

cp = '.;HermiT.jar;owlapi_5.1.17/*'
if sys.platform != 'win32':
    cp = '.:../HermiT.jar:../owlapi_5.1.17/*'

class solver:
    APE = '../APE/ape.exe'
    CP = cp
    SOLVER_CLASS = 'Solver'
    OWL_PATH = '../owl/'
    JAVA_PATH = '../jdk-16.0.2/bin/'
    lasterror = ''
    def solve(model, question):
        """
        take a story and a question and return the answers of the question

        @param:
        - model: str: file path of the story file that contains ACE sentences.
        - question: str: file path of the question  file that contains one ACE question sentence.
        
        @return:
        three tuples contain the answer individuals, subclasses and superclasses
        if the certain answer type contains nothing, an empty tuple will be return
        if the answer is not satisfiable, three empty tuple will be return
        if there is any error, the error message wiil be print and return None
        """
        #check ace files
        if type(model) != str or type(question) != str:
            solver.lasterror = 'Error! pass two vaild file path string.'
            return None
        if not os.path.exists(model) or not os.path.exists(question):
            solver.lasterror = 'Error! one of the given file was not found.'
            return None

        #ace2owl
        with concurrent.futures.ThreadPoolExecutor() as executor:
            f1 = executor.submit(solver.__ace2owl, model)
            f2 = executor.submit(solver.__ace2owl, question)
            try:
                f1.result()
                f2.result()
            except AssertionError as a:
                solver.lasterror = a.args[0]
                return None

        #check java file
        if not os.path.exists(solver.SOLVER_CLASS + '.class'):
            if not solver.compile():
                return None

        #run
        cmd = [
            solver.JAVA_PATH + 'java',
            '-cp',
            solver.CP,
            solver.SOLVER_CLASS,
            solver.OWL_PATH + os.path.basename(model) + '.owl',
            solver.OWL_PATH + os.path.basename(question) + '.owl'
        ]
        result = subprocess.run(cmd, capture_output = True)
        os.remove(solver.OWL_PATH + os.path.basename(model) + '.owl')
        os.remove(solver.OWL_PATH + os.path.basename(question) + '.owl')
        if b'' != result.stderr:
            solver.lasterror = result.stderr.decode('utf-8')
            return None
        elif 'Error!' == result.stdout.decode('utf-8')[:6]:
            solver.lasterror = result.stdout.decode('utf-8')
            return None

        #print(result.stdout.decode('utf-8'))
        return solver.__parseAnswer(result.stdout.decode('utf-8'))

    def compile():
        compile = subprocess.run([solver.JAVA_PATH + 'javac', '-cp', solver.CP, solver.SOLVER_CLASS + '.java'], capture_output = True)
        if b'' != compile.stderr:
            solver.lasterror = compile.stderr.decode('utf-8')
            return False
        return True

    def __ace2owl(f):
        cmd = [
            solver.APE,
            '-file',
            f,
            '-solo',
            'owlxml',
            '-guess'
            #'-noclex'
        ]
        result = subprocess.run(cmd, capture_output=True)
        result = result.stdout.decode('utf-8')

        assert not result.__contains__('importance="error"'), result

        with open(solver.OWL_PATH + os.path.basename(f) + '.owl', 'w') as file:
            file.write(result)

    def __parseAnswer(ans):
        ans = ans.split('$')
        #print(ans)
        rtn = [[],[],[]]
        for i in range(len(ans)):
            if ans[i] != '':
                rtn[i] = ans[i].split('*')

        #for s in rtn:
        #    print(s)
        
        for i in range(len(rtn)):
            for j in range(len(rtn[i]) - 1, -1, -1):
                rtn[i][j] = solver.__parseSentence(rtn[i][j])
                if solver.__isAPENamedInv(rtn[i][j]):
                    rtn[i].pop(j)
            rtn[i] = tuple(rtn[i])
        rtn = tuple(rtn)
        return rtn

    def __parseSentence(s):
        return s[s.index('#') + 1:-1]

    def __isAPENamedInv(s):
        if s[:3] == 'Ind' and s[3:].isdigit():
            return True
        return False

    def check(s):
        cmd = [
            solver.APE,
            '-text',
            s,
            '-solo',
            'owlxml',
            '-guess'
            #'-noclex'
        ]
        result = subprocess.run(cmd, capture_output=True)
        err = result.stderr.decode('utf-8')
        if err != '':
            return err
        result = result.stdout.decode('utf-8')
        print(err)
        #print(result)
        if result.__contains__('importance="error"'):
            return result
        return None