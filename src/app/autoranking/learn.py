'''
Experiment suite for learning and testing a new model. It comes along with the configuration
files to be found in /config/learning*

Created on Sep 19, 2014

@author: Eleftherios Avramidis
'''

import logging, sys
import os
from collections import OrderedDict
from ml.ranking import forname
from expsuite import PyExperimentSuite 
from sentence.parallelsentence import AttributeSet
from dataprocessor.ce.utils import join_jcml, fold_jcml_respect_ids
from dataprocessor.ce.cejcml import CEJcmlReader
from sentence import scoring
import cPickle as pickle

class RankingExperiment(PyExperimentSuite):
    
    restore_supported = True
    
    def reset(self, params, rep):
        self.restore_supported = True
        logging.info("Running in {}".format(os.getcwd()))
        logging.debug("params = {}".format(params))        
        #=======================================================================
        # get method-specific parameters
        #=======================================================================
        try:
            self.learner_params = eval(params["params_{}".format(params["learner"]).lower()])
        except:
            self.learner_params = {}
        
        logging.info("Accepted classifier parameters: {}\n".format(self.learner_params))
        
        #===============================================================================
        # get attributes
        #===============================================================================
        #self.meta_attributes = params["meta_attributes"].split(",")        
        #self.hidden_attributes = params["hidden_attributes"].split(",")
        self.discrete_attributes = params["discrete_attributes"].split(",")
        self.attribute_set = self._read_attributeset(params)
        
        
            
        
    def _join_or_link(self, source_path, source_datasets, ready_dataset):
        """
        Create a joined file from the given datasets if needed,
        or link them if they have already been given as one file
        """

        #get full path for all files
        source_datasets = [os.path.join(source_path, f) for f in source_datasets]
        logging.info("Source datasets: {}".format(source_datasets))
        if len(source_datasets)==1:
            logging.debug("Linking {} to {}".format(source_datasets[0], ready_dataset))
            logging.debug(os.listdir(os.curdir))
            try:
                os.symlink(source_datasets[0], ready_dataset)
            except OSError as e:
                if '[Errno 17]' in str(e):
                    logging.warn("Could not create symlink for data. [Errno 17] File exists")
                else:
                    raise Exception(e)
            
            
        else:
            logging.info("Joining training files")
            join_jcml(source_datasets, ready_dataset)
        
    
    def _read_attributeset(self, params):
        general_attributes = self._read_attributes(params, "general")
        source_attributes = self._read_attributes(params, "source")
        target_attributes = self._read_attributes(params, "target")    
        attribute_set = AttributeSet(general_attributes, source_attributes, target_attributes)
        return attribute_set
    
    def _read_attributes(self, params, key):
        attset = params["att"]
        attribute_key = "{}_{}".format(attset, key)
        attribute_names = params.setdefault(attribute_key, [])
        #print attribute_key
        #print attribute_names
        #print type(attribute_names)
        if attribute_names:
            attribute_names = attribute_names.split(',')
        else:
            attribute_names = []
        #print attribute_names
        return attribute_names
    
    def prepare_data(self, params, rep):
        """
        prepare training and test data depending on the test mode
        """
        training_sets = params["training_sets"].format(**params).split(',')
        training_path = params["training_path"].format(**params)
        dataset_filename = "{}.dataset.jcml".format(rep)
    
        self._join_or_link(training_path, training_sets, dataset_filename)
        
        #if cross validation is enabled
        if params["test"] == "crossvalidation":
            self.trainingset_filename = "{}.trainingset.jcml".format(rep)
            testset_filename = "{}.testset.jcml".format(rep)
            self.testset_filenames = [testset_filename]
            fold_jcml_respect_ids(dataset_filename,
                self.trainingset_filename,
                testset_filename,
                params['repetitions'],
                rep)
        
        #use only the last fold of a 10-fold cross-validation
        elif params["test"] == "last_tenth":
            self.trainingset_filename = "{}.trainingset.jcml".format(rep)
            testset_filename = "{}.testset.jcml".format(rep)
            self.testset_filenames = [testset_filename]
            fold_jcml_respect_ids(dataset_filename,
                self.trainingset_filename,
                testset_filename,
                10,
                0)
            
        #if a list of test-sets is given for testing upon
        elif params["test"] == "list":
            self.trainingset_filename = dataset_filename
            testset_filenames = params["test_sets"].format(**params).split(',')
            self.testset_filenames = [os.path.join(params["test_path"], f) for f in testset_filenames]
        
        #if no testing is required
        elif params["test"] == "None":
            self.trainingset_filename = dataset_filename
            self.testset_filenames = []
                
                
    def train(self, params, rep):
        """
        Load training data and train new ranking model
        """
        logging.info("Started training")
        params.update(self.learner_params)
        params["attribute_set"] = self.attribute_set
        params["scorers"] = params.setdefault("scorers", "").split(",")
        
        logging.info("train: Attribute_set before training: {}".format(params["attribute_set"]))
        
        output_filename = "{}.trainingset.tab".format(rep) 

        self.model_filename = "{}.model.dump".format(rep)
                                      
        logging.info("Fitting ranker based on {}".format(params["learner"]))                                                
        learner = params["learner"]
        ranker = forname(learner=learner)

        ranker.train(dataset_filename = self.trainingset_filename, 
                     output_filename = output_filename,
                     **params)
        
        logging.info("Ranker fitted sucessfully")                                              
        with open(self.model_filename, 'w') as f: 
            pickle.dump(ranker, f)
        
        logging.info("Extracting fitted coefficients")
        model_description = ranker.get_model_description()
        
        return model_description
        

    def test(self, params, rep):
        """
        Load test set and apply machine learning to assign labels
        """
        testset_input = self.testset_filenames[0]
        ranker = pickle.load(open(self.model_filename))

        self.testset_output_soft = "{}.testset_annotated_soft.jcml".format(rep)
        ranker.test(testset_input, self.testset_output_soft, reconstruct='soft', new_rank_name='rank_soft', **params)
    
        self.testset_output_hard = "{}.testset_annotated_hard.jcml".format(rep)
        ranker.test(testset_input, self.testset_output_hard, reconstruct='hard', new_rank_name='rank_hard', **params)
        
        return {}
    
    def evaluate(self, params, rep):
        """
        Load predictions (test) and analyze performance
        """
        class_name = params["class_name"]
        
        testset = CEJcmlReader(self.testset_output_soft, all_general=True, all_target=True) 
        scores = scoring.get_metrics_scores(testset, "rank_soft", class_name , prefix="soft", invert_ranks=False)
               
        testset = CEJcmlReader(self.testset_output_hard, all_general=True, all_target=True)        
        scores_hard = scoring.get_metrics_scores(testset, "rank_hard", class_name , prefix="hard", invert_ranks=False)
        
        scores.update(scores_hard)
        logging.debug("Scores: {}".format(scores))
        
        return scores
    
            
    
    def iterate(self, params, rep, n):
        ret = OrderedDict()
        logging.info("Running in {}".format(os.getcwd()))
        logging.info("Repetition: {}, Iteration: {}".format(rep, n))
        if n==0:
            self.prepare_data(params, rep)
        if n==1:
            ret.update(self.train(params, rep))
        if n==2:
            ret.update(self.test(params, rep))
        if n==3:
            ret.update(self.evaluate(params, rep))
        return ret
    
 
if __name__ == '__main__':
    loglevel = logging.INFO
    if "--debug" in sys.argv:
        loglevel = logging.DEBUG
    logging.basicConfig(level=loglevel,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

    # define a Handler which writes INFO messages or higher to the sys.stderr
    #console = logging.StreamHandler()
    #console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    #formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    #console.setFormatter(formatter)
    # add the handler to the root logger
    #logging.getLogger('').addHandler(console)
    FORMAT = "%(asctime)-15s [%(process)d:%(thread)d] %(message)s "
    #now = datetime.strftime(datetime.now(), "%Y-%m-%d_%H-%M-%S")
#    logging.basicConfig(filename='autoranking-{}.log'.format(now),level=logging.DEBUG, format=FORMAT)
#    sys.stderr = StreamToLogger(logging.getLogger('STDERR'), logging.INFO)
#    sys.stdout = StreamToLogger(logging.getLogger('STDOUT'), logging.INFO)
    mysuite = RankingExperiment();
    
    mysuite.start()
    #params = params =  {'params_svmeasylearner': "{'verbose':True}", 'test_path': '/home/dupo/taraxu_data/qualitative/', 'class_name': 'rank', 'iterations': 4, 'path': '/home/dupo/taraxu_data/qualitative/', 'langpair': 'de-en', 'discrete_attributes': 'src_reuse_status,src_terminologyAdmitted_status,src_total_status,src_spelling_status,src_style_status,src_grammar_status,src_terminology_status,src_resultStats_projectStatus,tgt-1_reuse_status,tgt-1_terminologyAdmitted_status,tgt-1_total_status,tgt-1_spelling_status,tgt-1_style_status,tgt-1_grammar_status,tgt-1_terminology_status,tgt-1_resultStats_projectStatus,tgt-2_reuse_status,tgt-2_terminologyAdmitted_status,tgt-2_total_status,tgt-2_spelling_status,tgt-2_style_status,tgt-2_grammar_status,tgt-2_terminology_status,tgt-2_resultStats_projectStatus', 'params_logreg': "{'stepwise_lr':True}", 'learner': 'LogRegLearner', 'experiment': 'grid', 'test': 'crossvalidation', 'test_sets': 'wmt2008-de-en-jcml-rank.all.analyzed.f.dev.jcml', 'attset_24_source': 'l_tokens', 'hidden_attributes': 'tgt-1_berkeley-tree,tgt-2_berkeley-tree,src_berkeley-tree,rank_diff,tgt-1_ref-lev,tgt-1_ref-meteor_score,tgt-1_ref-meteor_fragPenalty,tgt-1_ref-meteor_recall,tgt-1_ref-meteor_precision,tgt-1_ref-bleu,tgt-2_ref-lev,tgt-2_ref-meteor_score,tgt-2_ref-meteor_fragPenalty,tgt-2_ref-meteor_recall,tgt-2_ref-meteor_precision,tgt-2_ref-bleu,tgt-1_rank,tgt-2_rank', 'repetitions': 1, 'attset_24_target': 'cross-meteor_score,l_tokens,parse-VP', 'training_path': '/home/elav01/taraxu_data/qualitative/', 'tempdir': '/home/elav01/taraxu_data/qualitative/tmp', 'bidirectional_pairs': True, 'ties': False, 'training_sets': 'wmt2008-de-en-jcml-rank.all.analyzed.f.dev.jcml', 'remove_infinite': False, 'name': 'dev/learnerLogRegLearnerattattset_24', 'meta_attributes': 'testset,judgement_id,langsrc,langtgt,ps1_judgement_id,ps2_judgement_id,id,tgt-1_score,tgt-1_system,tgt-2_score,tgt-2_system,document_id,judge_id,segment_id', 'attset_24_general': None, 'att': 'attset_24'}
    #mysuite.reset(params, 1)
