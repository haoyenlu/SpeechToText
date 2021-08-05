#TODO

class TextProcessor():
    def __init__(self):
        self._text = ""
    def __iadd__(self,s):
        if type(s) is str:
            self._text += s
        return self

    @property
    def text(self):
        return self._text

    def tokenize_text(self):
        from nltk.tokenize import word_tokenize
        words = word_tokenize(self._text)
        return words

    

if __name__ == '__main__':
    sagan_quote = """If you wish to make an apple pie from scratch,you must first invent the universe."""
    tp = TextProcessor()
    tp += sagan_quote
    words = tp.tokenize_text()
    print(words)
