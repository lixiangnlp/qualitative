from loonybin import Tool

class TruecaseMoses(Tool):

    def getName(self):
        return 'Machine Translation/Monolingual Corpus/Truecase (Moses)'

    def getDescription(self):
        return ("Instead of lowercasing all training and test data, we may also want to keep words in their natural case, and only change the words at the beginning of their sentence to their most frequent form. This is what we mean by truecasing. Again, this requires first the training of a truecasing model, which is a list of words and the frequency of their different forms. ")

    def getRequiredPaths(self):
        return ["moses-scripts"]

    def getParamNames(self):
        return []

    def getInputNames(self, params):
        return [("truecaseModel", "A truecasing model, which is a list of words and the frequency of their different uppercase/lowercase forms. "),
                ("tokenizedCorpus", "Source side of the corpus in a tokenized form")]

    def getOutputNames(self, params):
        return [("truecasedCorpus", "Source side of the corpus in a truecased form")]

    def getPreAnalyzers(self, params, inputs):
        return ['perl echo TokenizedCorpusWordCount `wc -w %(tokenizedCorpus)s`'%(inputs),
		'echo TokenizedCorpusLineCount `wc -l %(tokenizedCorpus)s`'%(inputs)]

    def getCommands(self, params, inputs, outputs, paths):
        return ['perl ./recaser/truecase.perl --model %s < %s > %s ' % (input["truecaseModel"], inputs["tokenizedCorpus"], outputs["recasedCorpus"])]



if __name__ == '__main__':
    import sys
    t = TruecaseMoses();
    t.handle(sys.argv)
