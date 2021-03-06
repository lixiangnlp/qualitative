# -*- coding: utf-8 -*-

'''
This script provides
 (a) the class that wraps the functionality of the ranking mechanism
 (b) a command-line interactive interface for testing installation

Created on 2 Aug 2013

@author: Eleftherios Avramidis
'''

import time
import sys
import logging as log

from featuregenerator.blackbox.parser.berkeley.berkeleyclient import BerkeleyLocalFeatureGenerator
from sentence.sentence import SimpleSentence

from ml.lib.orange.ranking import OrangeRanker 
from sentence.parallelsentence import ParallelSentence

from bootstrap import ExperimentConfigParser
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


# 
# class Autoranking:
#     """
#     A class that demonstrates the use of simple ranking pipeline. It provides
#     the function 'parse' that receives source and translation strings and
#     returns a ranked list
#     @ivar featuregenerators: List of initialized feature generator objects in the order that will be used 
#     @type featuregenerators: [featuregenerator.featuregenerator.FeatureGenerator, ...]
#     @ivar ranker: Machine Learning class that handles ranking of items
#     @type ranker: ml.lib.orange
#     @ivar source_language: Language code for source language
#     @type source_language: str
#     @ivar target_language: Language code for target language
#     @type target_language: str
#     """
#     def __init__(self, config_files, model, source_language=None, 
#                  target_language=None, reverse=False):
#         """
#         Initialize the class.
#         @param config_files: a list of annotation configuration files that contain
#         the settings for all feature generators etc.
#         @type config_files: list(str)
#         @param model: the filename of the model of a picked learner object
#         @type model: str
#         @param source_language: Language code for source language
#         @type source_language: str
#         @param target_language: Language code for target language
#         @type target_language: str
#         """
#         #TODO: shouldn't the language pair also be stored along with the model?
# 
#         #retrieve the ranking model from the given file
#         try:
#             self.ranker = pickle.load(model)
#         except:
#             self.ranker = pickle.load(open(model))
#         
#         #read configuration for language resources
#         config = SafeConfigParser({'java': 'java'})
#         config.read(config_files)
#         
#         #initialize a java gateway 
#         #TODO: find a way to avoid loading java if not required by generators
#         gateway = JavaGateway(config.get("general", "java"))
#         
#         #whether the ranks should be reversed before used
#         #NOT supported
#         self.reverse = reverse
#         
#         #get the required attributes
#         self.featureset = self.ranker.attribute_set
#         featuregenerator_manager = FeatureGeneratorManager()
#         self.pipeline = featuregenerator_manager.get_parallel_features_pipeline(self.featureset, config, source_language, target_language, gateway)
#         
#     def rank_strings(self, source, translations, reconstruct='soft'):
#         """
#         Rank translations according to their estimated quality
#         @param source: The source sentence whose translations are ranked
#         @type source: C{str}
#         @param translations: The translations to be ranked
#         @type translations: [C{str}, ...]
#         """
#         sourcesentence = SimpleSentence(source)
#         translationsentences = [SimpleSentence(t, {"system" : "{}".format(i+1)}) for i,t in enumerate(translations)]
#         atts = {"langsrc" : self.source_language, "langtgt" : self.target_language}
#         parallelsentence = ParallelSentence(sourcesentence, translationsentences, None, atts)
#         return self.rank_parallelsentence(parallelsentence)
# 
#     def rank_parallelsentence(self, parallelsentence):
#         #annotate the parallelsentence
#         annotated_parallelsentence = self.pipeline.annotate_parallelsentence(parallelsentence)
#         log.info("line annotated")
#         
#         ranking, result_vector = self.ranker.get_ranked_sentence(annotated_parallelsentence)
#         
#         #put things in the original order given by the user
#         #because the ranker scrambles the order
#         ranking.sort(key=lambda x: x[1].get_attribute("system"))
#         
#         if self.reverse:
#             ranking.reverse()
#             
#         #return only ranks without system ids
#         result_vector["Final ranking"] = ([(r[0], r[1].get_system_name(), r[1].get_string()) for r in ranking])
#         ranking = [r[0] for r in ranking]
#         return ranking, result_vector
#     
#     def get_ranked_sentence(self, sourcesentence, translationsentences):
#         atts = {"langsrc":self.source_language, "langtgt":self.target_language}
#         parallelsentence = ParallelSentence(sourcesentence, translationsentences, None, atts)
#         annotated_parallelsentence = self._annotate(parallelsentence)
#         ranked_sentence, description = self.ranker.get_ranked_sentence(annotated_parallelsentence)
#         return ranked_sentence, description
#         
#     def _annotate(self, parallelsentence):
#         
#         #TODO: parallelize source target
#         #TODO: before parallelizing take care of diverse dependencies on preprocessing
#         for featuregenerator in self.featuregenerators:
#             log.debug("Annotating sentence with {} \n".format(str(featuregenerator)))
#             if featuregenerator:
#                 parallelsentence = featuregenerator.add_features_parallelsentence(parallelsentence)
#                 log.debug("Succesfully annotated sentence with {} \n".format(str(featuregenerator)))
#                 log.debug("Produced features: {} \n".format(parallelsentence))
#             else: 
#                 log.warn("Received inactive feature generator")
#         return parallelsentence
#         
        
#     def _get_parser(self, cfg, language):
#         for parser_name in [section for section in cfg.sections() if section.startswith("parser:")]:
#             if cfg.get(parser_name, "language") == language:
#                 grammarfile = cfg.get(parser_name, "grammarfile")
#                 sys.stderr.write("initializing socket parser with grammar file {}\n".format(grammarfile))
#                 return BerkeleyLocalFeatureGenerator(language, grammarfile, self.gateway)
#                 
#     def _get_java_gateway(self, cfg):
#         java_classpath, dir_path = cfg.get_classpath()
#         
#         if java_classpath:
#             
#             self.jvm = JVM(java_classpath)
#             socket_no = self.jvm.socket_no
#             self.gatewayclient = GatewayClient('localhost', socket_no)
#             self.gateway = JavaGateway(self.gatewayclient, auto_convert=True, auto_field=True)
#             sys.stderr.write("Initialized global Java gateway with pid {} in socket {}\n".format(self.jvm.pid, socket_no))
#             return self.gateway
# 
# 
#     def _old_initialize_featuregenerators(self, cfg):
#         """
#         Initialize the featuregenerators that handle superficial analysis of given translations
#         @param cfg: the loaded configuration object
#         """
#         source_language =  cfg.get("general", "source_language")
#         target_language =  cfg.get("general", "target_language")
#         
#         src_parser = cfg.get_parser(source_language)
#         tgt_parser = cfg.get_parser(target_language)
# 
#         langpair = (source_language, target_language)
#         
#         featuregenerators = [
#             Normalizer(source_language),
#             Normalizer(target_language),
#             Tokenizer(source_language),
#             Tokenizer(target_language),
#             
#             src_parser,
#             tgt_parser,
#             
#             ParserMatches(langpair),
#             
#             truecase only for the language model
#             Truecaser(source_language, cfg.get_truecaser_model(source_language)),
#             Truecaser(target_language, cfg.get_truecaser_model(target_language)),
#             
#             cfg.get_lm(source_language),
#             cfg.get_lm(target_language),            
# 
#             CrossMeteorGenerator(target_language, cfg.get_classpath()[0], cfg.get_classpath()[1]),
#             LengthFeatureGenerator()
#         ]
        
#        return featuregenerators
    

if __name__ == "__main__":


    loglevel = log.DEBUG
    log.basicConfig(level=loglevel,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M')

    try:
        classifier_filename = sys.argv[1] # "/share/taraxu/selection-mechanism/wmt13/sentenceranking/autoranking_wmt13_newfeatures1_de_en/class_nameranklangpairde-eninclude_references0.0ties0.0trainset_modeannotatedattattset_24classifierLogReg/classifier.clsf"
        configfilenames = sys.argv[2:]
    except:
        sys.exit("Syntax: python application.py <classifier_filename> <pipeline.config.1> [<pipeline.config.2> ...]")
    
    #[
    #'/home/Eleftherios Avramidis/workspace/qualitative/src/app/autoranking/config/pipeline.cfg',
    #'/home/Eleftherios Avramidis/workspace/qualitative/src/app/autoranking/config/pipeline.wmt13metric.blade6.de.de-en.cfg'
    #]
    
    
    autoranker = Autoranking(configfilenames, classifier_filename)
    
    while 1==1:    
        source = raw_input("Source sentence (or 'exit') > ")
        if source == "exit":
            sys.exit("Exit requested")
        doexit = False
        i = 0
        translations = []
        while 1==1:
            i+=1
            translation = raw_input("Translation (or empty to continue) > ")
            if translation!="":
                translations.append(translation)
            else:
                break

        result, description = autoranker.rank_strings(source, translations)
        print description
        print "The right order of the given sentences is ", result
