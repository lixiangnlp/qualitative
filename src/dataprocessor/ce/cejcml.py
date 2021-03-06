'''
Created on 26 Jun 2012

@author: Eleftherios Avramidis
'''

from numpy import average, std, min, max, asarray
import logging as log
from dataprocessor.datareader import DataReader

import sys
from collections import defaultdict, OrderedDict
from xml.etree.ElementTree import iterparse
from sentence.sentence import SimpleSentence
from sentence.parallelsentence import ParallelSentence, DefaultAttributeSet
from sentence.dataset import DataSet
import subprocess

def prefix_source_atts(source_attribute_names):
    return ["src_{}".format(att) for att in source_attribute_names]

def prefix_target_atts(target_attritube_names, target_index):
    return [["tgt-{}_{}".format(target_index, att) for att in target_attritube_names]]

def get_attribute_sets(filename):
    attribute_names = set()
    for parallelsentence in CEJcmlReader(filename).get_parallelsentences(compact=True, all_general=True, all_target=True):
        attribute_names.update((parallelsentence.get_source().get_attributes().keys()))
    return attribute_names


class CEJcmlReader(DataReader):
    """
    This class converts jcml format to tab format (orange format).
    The output file is saved to the same folder where input file is.
    """
    def __init__(self, input_xml_filename, **kwargs):
        """
        Init calls class SaxJcmlOrangeHeader for creating header and 
        SaxJcmlOrangeContent for creating content.
        @param input_xml_filename: name of input jcml file
        @type input_xml_filename: string
        @param class_name: name of class
        @type class_name: string
        @param desired_attributes: desired attributes
        @type desired_attributes: list of strings
        @param meta_attributes: meta attributes
        @type meta_attributes: list of strings
        """

        self.TAG_SENT = 'judgedsentence'
        self.TAG_SRC = 'src'
        self.TAG_TGT = 'tgt'
        self.TAG_REF = 'ref'
        self.TAG_DOC = 'jcml'

        self.desired_general = kwargs.setdefault('desired_general', ["rank","langsrc","langtgt","id","judgement_id"])
        self.desired_source = kwargs.setdefault("desired_source", [])
        self.desired_target = kwargs.setdefault('desired_target', ["system","rank_soft"])
        self.all_general = kwargs.setdefault('all_general', False)
        self.all_target = kwargs.setdefault('all_target', False)        
        log.debug("kwargs = {} ; self.all_target = {}".format(kwargs, self.all_target))
        self.input_filename = input_xml_filename
    
    def length(self):
        return self.__len__()
    
    def __len__(self):
        try:
            return int(subprocess.check_output(["grep", "-c", "<judgedsentence", self.input_filename]).strip())
        except:
            return 0 
    
#     def __len__(self):
#         """
#         This is a generator that reads the XML file incrementally and returns a parallel sentence object each time a new entry is read.
#         @param compact: do not read the strings of the encapsulate sentences (i.e. to save time and memory)
#         @type compact: C{boolean}
#         @return: an iterator of the read parallel sentences
#         @rtype: an C{iterator} of P{ParallelSentence}
#         """
# 
#         log.info("Started counting")
#         if hasattr(self.input_filename, "read"):
#             source_file = self.input_filename
#         else:
#             source_file = open(self.input_filename, "r")
#         # get an iterable
#         context = iterparse(source_file, events=("start", "end"))
#         # turn it into an iterator
#         context = iter(context)
# 
#         counter = 0
# 
#         for event, elem in context:
#             if event == "end" and elem.tag in self.TAG_SENT:
#                 counter += 1
#         log.info("Finished counting")
#         
#         if not hasattr(self.input_filename, "read"):
#             source_file.close()
#         
#         return counter
    
    def _separate_continuous_attributes(self, attributevectors):
        """
        Loop in dictionaries of an attribute vector per feature and separate continuous from discrete attributes
        based on their actual values
        """
        continuous_attribute_names = []
        discrete_attribute_names = []
        
        for key, values in attributevectors.iteritems():
            try:
                values = [float(v) for v in values]
                continuous_attribute_names.append(key)
            except ValueError:
                discrete_attribute_names.append(key)
        return continuous_attribute_names, discrete_attribute_names
    
    def get_attribute_sets(self, limit=None):
        """
        TODO: does not work!!!
        Attributes of parallel sentence files can be sparse, i.e. not all attributes appear in all sentences. Therefore
        in order to have a full descriptions of which attributes appear in a dataset, one has to parse the entire XML
        file, read the parallelsentences without the sentence strings, and gather the names (keys) of the seen attributes
        @return: an object of an attribute set,s containing the names of the features for source, target, parallel and 
        reference features
        @rtype: L{AttributeSet}
        """
        
        general_attributes, source_attributes, target_attributes, ref_attributes = self.get_attribute_vectors(limit=limit)
        general_continuous_attnames, general_discrete_attnames = self._separate_continuous_attributes(general_attributes)
        source_continuous_attnames, source_discrete_attnames = self._separate_continuous_attributes(source_attributes)
        target_continuous_attnames, target_discrete_attnames = self._separate_continuous_attributes(target_attributes)
        ref_continuous_attnames, ref_discrete_attnames = self._separate_continuous_attributes(ref_attributes)
        
        return DefaultAttributeSet(general_continuous_attnames, source_continuous_attnames, target_continuous_attnames, ref_continuous_attnames), \
            DefaultAttributeSet(general_discrete_attnames, source_discrete_attnames, target_discrete_attnames, ref_discrete_attnames)
       
    def get_attribute_names(self):
        """
        Get default ranking attribute set
        """
        parallel_attribute_names = set()
        source_attribute_names = set()
        target_attribute_names = set()
        ref_attribute_names = set()
        
        input_filename = self.input_filename
    
        xml_file = open(input_filename, "r")
        # get an iterable
        context = iterparse(xml_file, events=("start", "end"))
        # turn it into an iterator
        context = iter(context)
        # get the root element
        event, root = context.next()
        
        for event, elem in context:
            #new sentence: get attribute names
            attribute_names = elem.attrib.keys()
            if event == "start" and elem.tag == self.TAG_SENT:
                parallel_attribute_names.update(attribute_names)
            elif event == "start" and elem.tag == self.TAG_SRC:
                source_attribute_names.update(attribute_names)
            elif event == "start" and elem.tag == self.TAG_TGT:
                target_attribute_names.update(attribute_names)
            elif event == "start" and elem.tag == self.TAG_REF:
                ref_attribute_names.update(attribute_names)
            root.clear()            
        xml_file.close()
        return (parallel_attribute_names, source_attribute_names, 
                target_attribute_names, ref_attribute_names)
        
    def get_attribute_set(self):
        (parallel_attribute_names, 
         source_attribute_names, 
         target_attribute_names, 
         ref_attribute_names) = self.get_attribute_names()
        
        return DefaultAttributeSet(parallel_attribute_names, 
                            source_attribute_names, 
                            target_attribute_names, 
                            ref_attribute_names)
      
    def get_dataset(self, **kwargs):
        return DataSet(list(self.get_parallelsentences(**kwargs)))       

    def get_parallelsentences(self, compact=False):
        """
        This is a generator that reads the XML file incrementally and returns a parallel sentence object each time a new entry is read.
        @param compact: do not read the strings of the encapsulate sentences (i.e. to save time and memory)
        @type compact: C{boolean}
        @return: an iterator of the read parallel sentences
        @rtype: an C{iterator} of P{ParallelSentence}
        """
        
        if hasattr(self.input_filename, "read"):
            source_file = self.input_filename
            given_file = True
        else:
            source_file = open(self.input_filename, "r")
            given_file = False
        # get an iterable
        context = iterparse(source_file, events=("start", "end"))
        # turn it into an iterator
        context = iter(context)
        # get the root element
        event, root = context.next()
        
        attributes = []
        target_id = 0
        
        src_text = ""
        tgt_text = ""
        source_attributes = {}
        target_attributes = {}
        ref_attributes = {}    

        counter = 0

        for event, elem in context:
            #new sentence: get attributes
            if event == "start" and elem.tag == self.TAG_SENT:
                attributes = dict([(key, value) for key, value in elem.attrib.iteritems() if key in self.desired_general or self.all_general])
                targets = []
                src_text = None
                ref_text = None
            #new source sentence
            elif event == "start" and elem.tag == self.TAG_SRC:
                source_attributes = dict([(key, value) for key, value in elem.attrib.iteritems() if key in self.desired_source or self.all_target])

            elif event == "start" and elem.tag == self.TAG_REF:
                ref_attributes = dict([(key, value) for key, value in elem.attrib.iteritems() if key in self.desired_target or self.all_target])

            #new target sentence
            elif event == "start" and elem.tag == self.TAG_TGT:
                target_id += 1
                log.debug("self.all_target = {}".format(self.all_target))
                target_attributes = dict([(key, value) for key, value in elem.attrib.iteritems() if key in self.desired_target or self.all_target])
                log.debug("CEJcmlReader :: target_attributes = {}".format(target_attributes))
            elif not compact and event == "end" and elem.tag == self.TAG_SRC and elem.text:
                src_text = elem.text

            elif not compact and event == "end" and elem.tag == self.TAG_REF and elem.text:
                ref_text = elem.text
                #log.info("read reference text {}".format(ref_text))
 
                 
            elif event == "end" and elem.tag == self.TAG_TGT:
                if not compact and elem.text:
                    tgt_text = elem.text
                else:
                    tgt_text = ""
                target_sentence = SimpleSentence(tgt_text, target_attributes)
                targets.append(target_sentence)


            elif event == "end" and elem.tag in self.TAG_SENT:
                source = SimpleSentence(src_text, source_attributes)
                counter += 1
                ref = None
                if ref_text:
                    #log.info("Adding reference text {}".format(ref_text))
                    ref = SimpleSentence(ref_text, ref_attributes)
                else:
                    try:
                        log.debug("Reference is none in {} id:{}".format(self.input_filename, attributes["judgement_id"]))
                    except KeyError:
                        log.debug("Reference is none in {}:{}".format(self.input_filename, counter))
                parallelsentence = ParallelSentence(source, targets, ref, attributes)
                yield parallelsentence
            root.clear() 
            
        if not given_file:
            source_file.close()
        

    def fix(self, value):
        if self.remove_infinite:
            value = value.replace("inf", "9999999")
            value = value.replace("nan", "0")
        return value
           

   

            


# class CEJcmlStats:
#     """calculates statistics about specified attributes on an annotated JCML corpus. Low memory load"""
#     
#     def __init__(self, input_xml_filenames, **kwargs):
#     
#         self.TAG_SENT = 'judgedsentence'
#         self.TAG_SRC = 'src'
#         self.TAG_TGT = 'tgt'
#         self.TAG_DOC = 'jcml'
#     
#         self.input_filenames = input_xml_filenames
#         self.desired_general = kwargs.setdefault("desired_general", [])
#         self.desired_source = kwargs.setdefault("desired_source", [])
#         self.desired_target = kwargs.setdefault("desired_target", [])
#         self.desired_ref = kwargs.setdefault("desired_ref", [])
        
       
    def _print_statistics(self, key, values, fileobject=sys.stdout, show_discrete=False):
        try:
            values = asarray([float(v) for v in values])
        except:
            return

        f = {}
        functions = [len, average, std, min, max]
        for func in functions:
                try:
                    f[func.__name__] = func(values)
                except:
                    f[func.__name__] = -1
            
        display = "\t".join(["{:5.3f}".format(value) for name, value in f.iteritems()])

        fileobject.write("{}\t{}\n".format(key,display))
   
    
  
    def get_attribute_statistics(self, fileobject=sys.stdout, attribute_vectors=None):
        if not attribute_vectors:
            general_attributes, source_attributes, target_attributes, ref_attributes = self.get_attribute_vectors()
        else:
            general_attributes, source_attributes, target_attributes, ref_attributes = attribute_vectors
        
        for key, value in general_attributes.iteritems():
            self._print_statistics(key, value, fileobject)            
        
        for key, value in source_attributes.iteritems():
            self._print_statistics(key, value, fileobject)
                
        for key, value in target_attributes.iteritems():
            self._print_statistics(key, value, fileobject)            
                
    def get_attribute_vectors(self, limit=None):
        """
        Extract a list of values for each attribute
        """
        general_attributes = defaultdict(list)
        source_attributes = defaultdict(list)
        target_attributes = defaultdict(list)
        ref_attributes = defaultdict(list)
        
        input_filename = self.input_filename
    
        source_xml_file = open(input_filename, "r")
        # get an iterable
        context = iterparse(source_xml_file, events=("start", "end"))
        # turn it into an iterator
        context = iter(context)
        # get the root element
        event, root = context.next()
        
        counter=0
        
        for event, elem in context:
            #new sentence: get attributes
            if event == "start" and elem.tag == self.TAG_SENT:
                counter+=1
                if limit and counter>limit:
                    log.info("Finished extracting feature names from the first {} sentences".format(limit))
                    break
                for key, value in elem.attrib.iteritems():

               
                        general_attributes[key].append(value)
                    
            #new source sentence
            elif event == "start" and elem.tag == self.TAG_SRC:
                for key, value in elem.attrib.iteritems():

                        source_attributes[key].append(value)

            #new target sentence
            elif event == "start" and elem.tag == self.TAG_TGT:
                for key, value in elem.attrib.iteritems():

                        target_attributes[key].append(value)
                        
            elif event == "start" and elem.tag == self.TAG_REF:
                for key, value in elem.attrib.iteritems():

                        ref_attributes[key].append(value)

            root.clear()
            
        source_xml_file.close()
        
        return general_attributes, source_attributes, target_attributes, ref_attributes


def get_statistics(input_xml_filenames, **kwargs):
    vector = defaultdict(list)
    for input_xml_filename in input_xml_filenames:
        reader = CEJcmlReader(input_xml_filename, **kwargs)
        for parallelsentence in reader.get_parallelsentences(compact=True):
            general_attributes = parallelsentence.get_attributes()
            source_attributes = parallelsentence.get_source().get_attributes()
            source_attributes = dict([("src_{}".format(att), value) for att, value in source_attributes.iteritems()]) 
            try:
               ref_attributes = parallelsentence.get_reference().get_attributes()
            except:
               ref_attributes = {}
            
            general_attributes.update(source_attributes)
            general_attributes.update(ref_attributes)

            for att, value in general_attributes.iteritems():
                 vector[att].append(value)

            for target in parallelsentence.get_translations():                
                for att, value in target.get_attributes().iteritems():
                     vector["tgt_{}".format(att)].append(value)
    yield "feat \t avg \t std \t min \t max " 
    for att, values in vector.iteritems():    
        try:
            values = asarray([float(v) for v in values])
        except:
            continue
        yield "{} \t {:5.3f} \t {:5.3f} \t {:5.3f} ".format(
                                                           att,
                                                           average(values),
                                                           std(values),
                                                           min(values),
                                                           max(values)
                                                           )
