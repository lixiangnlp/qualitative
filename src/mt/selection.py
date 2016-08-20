'''
Created on 19 Apr 2016
@author: Eleftherios Avramidis
'''
import pickle

from app.autoranking.application import Autoranking
from featuregenerator.blackbox.counts import LengthFeatureGenerator
from featuregenerator.blackbox.ibm1 import Ibm1FeatureGenerator
from featuregenerator.blackbox.parser.berkeley.cfgrules import CfgAlignmentFeatureGenerator
from featuregenerator.blackbox.parser.berkeley.parsermatches import ParserMatches
from featuregenerator.preprocessor import Normalizer, Tokenizer, Truecaser
from featuregenerator.reference.meteor.meteor import CrossMeteorGenerator
from ConfigParser import SafeConfigParser

import time
import sys
import logging as log

from featuregenerator.blackbox.parser.berkeley.berkeleyclient import BerkeleyLocalFeatureGenerator
from sentence.sentence import SimpleSentence

from ml.lib.orange.ranking import OrangeRanker 
from sentence.parallelsentence import ParallelSentence

from featuregenerator.blackbox.parser.berkeley.parsermatches import ParserMatches
from featuregenerator.blackbox.counts import LengthFeatureGenerator
from featuregenerator.reference.meteor.meteor import CrossMeteorGenerator
from featuregenerator.preprocessor import Normalizer
from featuregenerator.preprocessor import Tokenizer
from featuregenerator.preprocessor import Truecaser

from py4j.java_gateway import GatewayClient, JavaGateway 
import pickle
from featuregenerator import FeatureGeneratorManager
from ConfigParser import SafeConfigParser
from util.jvm import LocalJavaGateway


class Autoranking:
    """
    A class that demonstrates the use of simple ranking pipeline. It provides
    the function 'parse' that receives source and translation strings and
    returns a ranked list
    @ivar featuregenerators: List of initialized feature generator objects in the order that will be used 
    @type featuregenerators: [featuregenerator.featuregenerator.FeatureGenerator, ...]
    @ivar ranker: Machine Learning class that handles ranking of items
    @type ranker: ml.lib.orange
    @ivar source_language: Language code for source language
    @type source_language: str
    @ivar target_language: Language code for target language
    @type target_language: str
    """
    def __init__(self, config_files, model, source_language=None, 
                 target_language=None, reverse=False):
        """
        Initialize the class.
        @param config_files: a list of annotation configuration files that contain
        the settings for all feature generators etc.
        @type config_files: list(str)
        @param model: the filename of the model of a picked learner object
        @type model: str
        @param source_language: Language code for source language
        @type source_language: str
        @param target_language: Language code for target language
        @type target_language: str
        """
        #TODO: shouldn't the language pair also be stored along with the model?

        #retrieve the ranking model from the given file
        try:
            self.ranker = pickle.load(model)
        except:
            self.ranker = pickle.load(open(model))
        
        #read configuration for language resources
        config = SafeConfigParser({'java': 'java'})
        config.read(config_files)
        
        #initialize a java gateway 
        #TODO: find a way to avoid loading java if not required by generators
        gateway = LocalJavaGateway(config.get("general", "java"))
        
        #whether the ranks should be reversed before used
        #NOT supported
        self.reverse = reverse
        
        #get the required attributes
        self.featureset = self.ranker.attribute_set
        featuregenerator_manager = FeatureGeneratorManager()
        self.pipeline = featuregenerator_manager.get_parallel_features_pipeline(self.featureset, config, source_language, target_language, gateway)
        self.featuregenerators = self.pipeline[0] + self.pipeline[1] + self.pipeline[2]
        
        self.preprocessors = [
            Normalizer(source_language),
            Normalizer(target_language),
            Tokenizer(source_language),
            Tokenizer(target_language),
            Truecaser(source_language, config.get("Truecaser:{}".format(source_language), model)),
            Truecaser(target_language, config.get("Truecaser:{}".format(target_language), model)),
        ]
        
    def rank_strings(self, source, translations, reconstruct='soft'):
        """
        Rank translations according to their estimated quality
        @param source: The source sentence whose translations are ranked
        @type source: C{str}
        @param translations: The translations to be ranked
        @type translations: [C{str}, ...]
        """
        sourcesentence = SimpleSentence(source)
        translationsentences = [SimpleSentence(t, {"system" : "{}".format(i+1)}) for i,t in enumerate(translations)]
        atts = {"langsrc" : self.source_language, "langtgt" : self.target_language}
        parallelsentence = ParallelSentence(sourcesentence, translationsentences, None, atts)
        return self.rank_parallelsentence(parallelsentence)
    
    def rank_parallelsentence(self, parallelsentence):
        #annotate the parallelsentence
        annotated_parallelsentence = self._annotate(parallelsentence)
        log.info("line annotated")
        ranking, description = self.ranker.rank_sentence(annotated_parallelsentence)
        
        #put things in the original order given by the user
        #because the ranker scrambles the order
        ranking.sort(key=lambda x: x[1].get_attribute("system"))
        
        if self.reverse:
            ranking.reverse()
            
        #return only ranks without system ids
        description += "Final ranking: {}".format([(r[0], r[1].get_system_name(), r[1].get_string()) for r in ranking])
        ranking = [r[0] for r in ranking]
        return ranking, description
    
    def get_ranked_sentence(self, sourcesentence, translationsentences):
        atts = {"langsrc":self.source_language, "langtgt":self.target_language}
        parallelsentence = ParallelSentence(sourcesentence, translationsentences, None, atts)
        annotated_parallelsentence = self._annotate(parallelsentence)
        ranked_sentence, description = self.ranker.get_ranked_sentence(annotated_parallelsentence)
        return ranked_sentence, description
        
    def _annotate(self, parallelsentence):
        
        #TODO: parallelize source target
        #TODO: before parallelizing take care of diverse dependencies on preprocessing

        for preprocessor in self.preprocessors:
            parallelsentence = preprocessor.add_features_parallelsentence(parallelsentence)
        
        for featuregenerator in self.featuregenerators:
            sys.stderr.write("Running {} \n".format(str(featuregenerator)))
            if featuregenerator:
                parallelsentence = featuregenerator.add_features_parallelsentence(parallelsentence)
                log.info("got sentence")
            else: 
                log.warn("Received inactive feature generator")
        return parallelsentence
        