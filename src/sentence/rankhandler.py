'''
Created on Apr 15, 2011

@author: Eleftherios Avramidis
'''

from parallelsentence import ParallelSentence


class RankHandler(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
      
    def get_multiclass_from_pairwise_set(self, parallelsentences, allow_ties = False):
        sentences_per_judgment = {}
        #constract groups of pairwise sentences, based on their judgment id, which is unique per group
        for parallelsentence in parallelsentences:
            jid = int(parallelsentence.get_attribute("judgement_id"))
            if jid in sentences_per_judgment:
                sentences_per_judgment[jid].append(parallelsentence)
            else:
                #if this key has not been seen before, initiate a new entry
                sentences_per_judgment[jid]=[parallelsentence]
        
        for jid in sentences_per_judgment:
            pairwise_sentences = sentences_per_judgment[jid]
            translation_by_system = {}
            for pairwise_sentence in pairwise_sentences:
                #it is supposed to have only two translations
                translation1 = pairwise_sentence.get_translations()[0]
                translation2 = pairwise_sentence.get_translations()[1]
                
                translation_by_system[translation1.get_attribute("system")] = translation1
                
                
                
            
            
            
            
        
    
    def get_pairwise_from_multiclass_sentence(self, parallelsentence, judgement_id, allow_ties = False):
        """
        Converts a the ranked system translations of one sentence into many sentences containing one translation pair each,
        so that system output can be compared in a pairwise manner. 
        @param parallelsentence: the parallesentences than needs to be split into pairs
        @type parallelsentence: ParallelSentence
        @param allow_ties: sentences of equal performance (rank=0) will be included in the set, if this is set to True
        @type allow_ties: boolean
        @return a list of parallelsentences containing a pair of system translations and a universal rank value 
        """
        source = parallelsentence.get_source()
        translations = parallelsentence.get_translations()
        pairwise_sentences = []
    
        for system_a  in translations:
            for system_b in translations:
                if system_a == system_b:
                    continue
                rank = self.__normalize_rank__(system_a, system_b)
                if rank != "0" or allow_ties:
                    new_attributes = parallelsentence.get_attributes()
                    new_attributes["rank"] = rank 
                    new_attributes["judgement_id"] = judgement_id
                    pairwise_sentence = ParallelSentence(source, [system_a, system_b], None, new_attributes) 
                    pairwise_sentences.append(pairwise_sentence)
        
        for system in translations:
            #remove existing ranks
            system.del_attribute("rank")
        
        return pairwise_sentences
                
    
    def get_pairwise_from_multiclass_set(self, parallelsentences, allow_ties = False):
        pairwise_parallelsentences = []
        j = 0
        for parallelsentence in parallelsentences: 
            j += 1
            if "judgment_id" in parallelsentence.get_attributes():
                judgement_id = parallelsentence.get_attribute("judgment_id")
            else
                judgement_id = j
            pairwise_parallelsentences.extend( self.get_pairwise_from_multiclass_sentence(parallelsentence, judgement_id, allow_ties) )
        return pairwise_parallelsentences
            
    
    
    
    def __normalize_rank__(self, system_a, system_b):
        """
        Receives two rank scores for the two respective system outputs, compares them and returns a universal
        comparison value, namely -1 if the first system is better, +1 if the second system output is better, 
        and 0 if they are equally good. 
        """
        rank_a = system_a.get_attribute("rank")
        rank_b = system_b.get_attribute("rank")
        if rank_a < rank_b:
            rank = "-1"
        elif rank_a > rank_b:
            rank = "1"
        else:
            rank = "0"       
        return rank
        
        
        