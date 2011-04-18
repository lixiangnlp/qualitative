"""

@author: Eleftherios Avramidis
"""
from __future__ import division
from featuregenerator import FeatureGenerator
from nltk.tokenize.punkt import PunktWordTokenizer


class DiffGenerator(FeatureGenerator):
    """
    Computes tgt difference for numerical features with the same name
    """


    def get_features_parallelsentence(self, parallelsentence):
        """
        Gets executed once per parallel sentence. Performs substraction of the respective numerical features of the 2 target sentences.
        Features with the same name get substracted and the new feature gets added to the level of the parallel sentence.
        @param parallesentence: the object of the parallelsentence, already containing the simplesentences for the target translations
        @type parallelsentence: sentence.parallelsentence.ParallelSentence  
        """
        translations = parallelsentence.get_translations()
        ps_attributes = {}
        if len(translations)!=2: #diff features make sense only for pairwise comparisons
            return ps_attributes
        tgt1_attributes = translations[0].get_attributes()
        tgt2_attributes = translations[1].get_attributes()
        for tgt1_attribute_key in tgt1_attributes:
            if tgt1_attribute_key in tgt2_attributes:
                #Check if the attribute is actually a float/int number
                try: 
                    tgt1_value = float(tgt1_attributes[tgt1_attribute_key])
                    tgt2_value = float(tgt2_attributes[tgt1_attribute_key])
                except ValueError:
                    #if not possible, jump to the next attribute
                    continue 
                #calculate difference
                diff = tgt2_value - tgt1_value
                att_name = "%s_diff" % tgt1_attribute_key
                ps_attributes[att_name] = str(diff)
        return ps_attributes
                    
   
        