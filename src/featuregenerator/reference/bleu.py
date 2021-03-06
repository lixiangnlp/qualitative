'''
BLEU computation functions in python
@author: Eleftherios Avramidis
@note: Modified copy from Hieu Hoang's code for Moses Project

Provides:
cook_refs(refs, n=4): Transform a list of reference sentences as strings into a form usable by cook_test().
cook_test(test, refs, n=4): Transform a test sentence as a string (together with the cooked reference sentences) into a form usable by score_cooked().
score_cooked(alltest, n=4): Score a list of cooked test sentences.

score_set(s, testid, refids, n=4): Interface with dataset.py; calculate BLEU score of testid against refids.

The reason for breaking the BLEU computation into three phases cook_refs(), cook_test(), and score_cooked() 
is to allow the caller to calculate BLEU scores for multiple test sets as efficiently as possible.
'''

import sys, math, re, xml.sax.saxutils
sys.path.append('/fs/clip-mteval/Programs/hiero')
#import dataset
#import log

# Added to bypass NIST-style pre-processing of hyp and ref files -- wade
nonorm = 0

preserve_case = False
eff_ref_len = "shortest"

normalize1 = [
    ('<skipped>', ''),         # strip "skipped" tags
    (r'-\n', ''),              # strip end-of-line hyphenation and join lines
    (r'\n', ' '),              # join lines
#    (r'(\d)\s+(?=\d)', r'\1'), # join digits
]
normalize1 = [(re.compile(pattern), replace) for (pattern, replace) in normalize1]

normalize2 = [
    (r'([\{-\~\[-\` -\&\(-\+\:-\@\/])',r' \1 '), # tokenize punctuation. apostrophe is missing
    (r'([^0-9])([\.,])',r'\1 \2 '),              # tokenize period and comma unless preceded by a digit
    (r'([\.,])([^0-9])',r' \1 \2'),              # tokenize period and comma unless followed by a digit
    (r'([0-9])(-)',r'\1 \2 ')                    # tokenize dash when preceded by a digit
]
normalize2 = [(re.compile(pattern), replace) for (pattern, replace) in normalize2]

def normalize(s):
    '''Normalize and tokenize text. This is lifted from NIST mteval-v11a.pl.'''
    # Added to bypass NIST-style pre-processing of hyp and ref files -- wade
    if (nonorm):
        return s.split()
    
    if not isinstance(s, basestring):
        s = " ".join(s)
    # language-independent part:
    for (pattern, replace) in normalize1:
        s = re.sub(pattern, replace, s)
    s = xml.sax.saxutils.unescape(s, {'&quot;':'"'})
    # language-dependent part (assuming Western languages):
    s = " %s " % s
    if not preserve_case:
        s = s.lower()         # this might not be identical to the original
    for (pattern, replace) in normalize2:
        s = re.sub(pattern, replace, s)
    return s.split()

def count_ngrams(words, n=4):
    counts = {}
    for k in xrange(1,n+1):
        for i in xrange(len(words)-k+1):
            ngram = tuple(words[i:i+k])
            counts[ngram] = counts.get(ngram, 0)+1
    return counts
    
def cook_refs(refs, n=4):
    '''Takes a list of reference sentences for a single segment
    and returns an object that encapsulates everything that BLEU
    needs to know about them.'''
    
    refs = [normalize(ref) for ref in refs]
    maxcounts = {}
    for ref in refs:
        counts = count_ngrams(ref, n)
        for (ngram,count) in counts.iteritems():
            maxcounts[ngram] = max(maxcounts.get(ngram,0), count)
    return ([len(ref) for ref in refs], maxcounts)

def cook_test(test, (reflens, refmaxcounts), n=4):
    '''Takes a test sentence and returns an object that
    encapsulates everything that BLEU needs to know about it.'''
    
    test = normalize(test)
    result = {}
    result["testlen"] = len(test)

    # Calculate effective reference sentence length.
    
    if eff_ref_len == "shortest":
        result["reflen"] = min(reflens)
    elif eff_ref_len == "average":
        result["reflen"] = float(sum(reflens))/len(reflens)
    elif eff_ref_len == "closest":
        min_diff = None
        for reflen in reflens:
            if min_diff is None or abs(reflen-len(test)) < min_diff:
                min_diff = abs(reflen-len(test))
                result['reflen'] = reflen

    result["guess"] = [max(len(test)-k+1,0) for k in xrange(1,n+1)]

    result['correct'] = [0]*n
    counts = count_ngrams(test, n)
    for (ngram, count) in counts.iteritems():
        result["correct"][len(ngram)-1] += min(refmaxcounts.get(ngram,0), count)

    return result

def score_cooked(allcomps, n=4):
    totalcomps = {'testlen':0, 'reflen':0, 'guess':[0]*n, 'correct':[0]*n}
    for comps in allcomps:
        for key in ['testlen','reflen']:
            totalcomps[key] += comps[key]
        for key in ['guess','correct']:
            for k in xrange(n):
                totalcomps[key][k] += comps[key][k]
    logbleu = 0.0
    for k in xrange(n):
        if totalcomps['correct'][k] == 0:
            return 0.0
#        log.write("%d-grams: %f\n" % (k,float(totalcomps['correct'][k])/totalcomps['guess'][k]))
        logbleu += math.log(totalcomps['correct'][k])-math.log(totalcomps['guess'][k])
    logbleu /= float(n)
#    log.write("Effective reference length: %d test length: %d\n" % (totalcomps['reflen'], totalcomps['testlen']))
    logbleu += min(0,1-float(totalcomps['reflen'])/totalcomps['testlen'])
    return math.exp(logbleu)


def smoothed_score_cooked(allcomps, n=4):
    totalcomps = {'testlen':0, 'reflen':0, 'guess':[0]*n, 'correct':[0]*n}
    for comps in allcomps:
        for key in ['testlen','reflen']:
            totalcomps[key] += comps[key]
        for key in ['guess','correct']:
            for k in xrange(n):
                totalcomps[key][k] += comps[key][k]
    logbleu = 0.0
    for k in xrange(n):
        if totalcomps['correct'][k] == 0:
            return 0.0
#        log.write("%d-grams: %f\n" % (k,float(totalcomps['correct'][k])/totalcomps['guess'][k]))
        logbleu += math.log(totalcomps['correct'][k]+1)-math.log(totalcomps['guess'][k])
    logbleu /= float(n+1)
#    log.write("Effective reference length: %d test length: %d\n" % (totalcomps['reflen'], totalcomps['testlen']))
    logbleu += min(0,1-float(totalcomps['reflen'])/totalcomps['testlen'])
    return math.exp(logbleu)




def smoothed_score_sentence(translation, references, n=4):
    """
    Provides the single-sentence BLEU score for one sentence, given n references 
    @param translation: Translation text that needs to be evaluated 
    @type translation: str
    @param references: List of reference translations to be used for the evaluation
    @type references: [str, ...]
    """
    r = len(references)
    if r == 0:
        return 0.00
    references = cook_refs(references, n)
    test_set = cook_test(translation, references, n)
    return smoothed_score_cooked([test_set], n)

def score_sentence(translation, references, n=4):
    """
    Provides the single-sentence BLEU score for one sentence, given n references 
    @param translation: Translation text that needs to be evaluated 
    @type translation: str
    @param references: List of reference translations to be used for the evaluation
    @type references: [str, ...]
    @return: BLEU score for sentence
    @rtype: float
    """
    r = len(references)
    if r == 0:
        return 0.00
    references = cook_refs(references, n)
    test_set = cook_test(translation, references, n)
    return score_cooked([test_set], n)
    
def score_sentences(sentence_tuples, n=4):
    """
    Provides BLEU calculation for many sentences.  
    @param sentence_tuples: a list of tuples generated out of the translated sentences. Each
    tuple should contain one translated sentence and its list of references.
    @type sentence_tuples: [tuple(str(translation), [str(reference), ...]), ...]
    @return: BLEU score for many sentences
    @rtype: float 
    """
    
    cooked_tests = []
     
    for translation, references in sentence_tuples:
        r = len(references)
        if r == 0:
            continue
        cooked_references = cook_refs(references, n)
        cooked_tests.append(cook_test(translation, cooked_references, n))
    return score_cooked(cooked_tests, n)
        

def score_multitarget_sentences(sentence_tuples, n=4):

    import numpy as np
    cooked_tests = []
    
    for translations, references in sentence_tuples:
        r = len(references)
        if r == 0:
            continue
        cooked_references = cook_refs(references, n)

        guess = {}
        correct = {}
        cooked_translations = []
        
        for translation in translations:
            cooked_translation = cook_test(translation, cooked_references, n)
            cooked_translations.append(cooked_translation)
#            guesses.append(cooked_translation['guess'])
            i = 0
            for value in cooked_translation['correct']:                
                correct.setdefault(i, []).append(value)
                i+=1
            
            i = 0 
            for value in cooked_translation['guess']:                
                guess.setdefault(i, []).append(value)
                i+=1
#            
#            testlen.append(cooked_translation['testlen'])
        
            
        
        
        avg_translation = {
                           'guess' : [min(values) for key, values in guess.iteritems()],
                           'testlen': min([t['testlen'] for t in cooked_translations]),
                           'reflen': cooked_translation['reflen'],
                           'correct': [min(values) for key, values in correct.iteritems()],
                           }

        cooked_tests.append(avg_translation)
    return score_cooked(cooked_tests, n)


from featuregenerator import FeatureGenerator

from collections import OrderedDict


class BleuGenerator(FeatureGenerator):
    '''
    Provides BLEU score against the reference
    '''
    feature_names = ['ref-bleu']
    
    def get_features_tgt(self, target, parallelsentence):
        """
        Calculates BLEU score for the given target sentence, against the reference sentence
        @param simplesentence: The target sentence to be scored
        @type simplesentence: sentence.sentence.SimpleSentence
        @rtype: dict
        @return: dictionary containing Levenshtein distance as an attribute 
        """
        target_untokenized = target.get_string()
        try:
            ref_untokenized = parallelsentence.get_reference().get_string()

            bleu_value = score_sentence(target_untokenized, [ref_untokenized])
            return {'ref-bleu': '{:.4}'.format(bleu_value)}
        except:
            return {}
    
    def analytic_score_sentences(self, sentence_tuples):
        scores = OrderedDict()
        for n in range (1,6):
            scores["bleu-{}gram".format(n)] = score_sentences(sentence_tuples, n)
        return scores 



class CrossBleuGenerator(FeatureGenerator):
    '''
    Provides cross-BLEU score of the current target sentence against the others
    '''
    feature_names = ['cross-bleu']
    
    def get_features_tgt(self, translation, parallelsentence):
        current_system_name = translation.get_attribute("system")
        alltranslations = dict([(t.get_attribute("system"), t.get_string()) for t in parallelsentence.get_translations()])
        del(alltranslations[current_system_name])
        references = alltranslations.values()
        bleu_value = score_sentence(translation.get_string(), references)
        return {'cross-bleu': '{:.4}'.format(bleu_value)}
        
            
            
        
        
        
        
    

#from nltk.tokenize.punkt import PunktWordTokenizer 
#from tempfile import mktemp

#from os import unlink 
#import os
#import subprocess
#import sys
#import codecs
#    def bleu(self, translation, reference):
#        
#        translation = " ".join(PunktWordTokenizer().tokenize(translation))
#        tfilename = mktemp(dir=u'/tmp/', suffix=u'.tgt.txt')
#        tfile = codecs.open(tfilename, 'w', 'utf-8')
#        tfile.write(translation)
#        tfile.close()
#        
#        reference = " ".join(PunktWordTokenizer().tokenize(reference))
#        rfilename = mktemp(dir=u'/tmp/', suffix=u'.ref.txt')
#        rfile = codecs.open(rfilename, 'w', 'utf-8')
#        rfile.write(reference)
#        rfile.close()
#        
#        ofilename = mktemp(dir=u'/tmp/', suffix=u'.out.txt')
#        ofile = codecs.open(ofilename, 'w', 'utf-8')
#        
#        path = os.path.dirname(__file__)
#        bleupath = os.path.join(path, "bleu")
#        print bleupath
#        subprocess.call([bleupath, "-s" , "-p", "-S", "-r", rfilename, tfilename], stdout = ofile)
#        ofile.close()
#        ofile = codecs.open(ofilename, 'r', 'utf-8')
#        output = ofile.readline()
#        output = float(output)
#        return output
#
#        
        


    
        

        
    
#def score_set(set, testid, refids, n=4):
#    alltest = []
#    for seg in set.segs():
#        try:
#            test = seg.versions[testid].words
#        except KeyError:
##            log.write("Warning: missing test sentence\n")
#            continue
#        try:
#            refs = [seg.versions[refid].words for refid in refids]
#        except KeyError:
#            pass
##            log.write("Warning: missing reference sentence, %s\n" % seg.id)
#        refs = cook_refs(refs, n)
#        alltest.append(cook_test(test, refs, n))
##    log.write("%d sentences\n" % len(alltest))
#    return score_cooked(alltest, n)

#if __name__ == "__main__":
##    import psyco
##    psyco.full()
#
#    import getopt
#    raw_test = False
#    (opts,args) = getopt.getopt(sys.argv[1:], "rc", [])
#    for (opt,parm) in opts:
#        if opt == "-r":
#            raw_test = True
#        elif opt == "-c":
#            preserve_case = True
#    
#    s = dataset.Dataset()
#    if args[0] == '-':
#        infile = sys.stdin
#    else:
#        infile = args[0]
#    if raw_test:
#        (root, testids) = s.read_raw(infile, docid='whatever', sysid='testsys')
#    else:
#        (root, testids) = s.read(infile)
#    print "Test systems: %s" % ", ".join(testids)
#    (root, refids) = s.read(args[1])
#    print "Reference systems: %s" % ", ".join(refids)
#    
#    for testid in testids:
#        print "BLEU score: ", score_set(s, testid, refids)
#            
    
