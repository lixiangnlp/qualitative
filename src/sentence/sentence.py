#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Provides the class which contains the information for a simple (shallow) sentence
@author: Eleftherios Avramidis
"""

from copy import deepcopy
import logging as log
from collections import OrderedDict
import unicodedata

class SimpleSentence(object):
    """
    A simple (shallow) sentence object, which wraps both a sentence and its attributes
    @ivar string: the string that the simple sentence will consist of
    @type string: string
    @ivar attributes: a dictionary of arguments that describe properties of the simple sentence
    @type attributes: {str, Object}
    """


    def __init__(self, string="", attributes=OrderedDict()):
        """
        Initializes a simple (shallow) sentence object, which wraps both a sentence and its attributes
        @param string: the string that the simple sentence will consist of
        @type string: string
        @param attributes: a dictionary of arguments that describe properties of the simple sentence
        @type attributes: {str, Object}
        
        """
        #avoid tabs
        if not string:
            string = ""
        self.string = string.replace("\t", "  ")
        #avoid getting a shallow reference to the attributes in the dict
        self.attributes = deepcopy (attributes) 
    
#    def __gt__(self, other):
#        return self.attributes["system"] > other.attributes["system"]
    
#    def __lt__(self, other):
#        return self.attributes["system"] < other.attributes["system"]
    
    def __eq__(self, other):
        return (self.string == other.string and self.attributes == other.attributes)
    
    def get_string(self):
        """
        Get the string of this simple sentence
        @return: the text contained in the simple sentence
        @rtype: String
        """
        return self.string
    
    def get_attributes(self):
        """
        Get the attributes of this sentence
        @return: a dictionary of attributes that describe properties of the sentence
        @rtype: dict
        """
        return self.attributes

    def get_rank(self):
        """
        Get the rank attribute of the sentence
        @return: the rank attribute of the sentence
        @rtype: str
        """
        return self.attributes["rank"]
    

    def get_system_name(self):
        return self.attributes["system"]

    def add_attribute(self, key, value):
        self.attributes[key] = value

    def get_attribute(self, key, sub=None):
        try:
            return self.attributes[key]
        except KeyError:
            if sub:
                return sub
            else:
                raise KeyError("Could not find attribute '{}' , atts={}".format(key, self.attributes))              
    
    def add_attributes(self, attributes):
        self.attributes.update(attributes)
    
    def rename_attribute(self, old_name, new_name):
        self.attributes[new_name] = self.attributes[old_name]
        del(self.attributes[old_name])
        
    def del_attribute(self, attribute):
        del(self.attributes[attribute])

    def keep_only_attributes(self, attribute_names):
        """
        Modiify current sentence object by removing sentence attributes whose name is not in the given list
        @param attribute_names: a list of attribute names that we want to keep
        @type attribute_names: [str, ...]
        """
        for name in self.attributes.keys():
            if name not in attribute_names:
                del(self.attributes[name])
            
        
    def __str__(self):
        return self.string + ": " + str(self.attributes)
    
    def merge_simplesentence(self, ss, attribute_replacements = {}):
        """
        Add the attributes to the object SimpleSentence(). In place
        @param attr: attributes of a simple sentence
        @type attr: dict 
        """
        
        incoming_attributes = ss.get_attributes()
        for incoming_attribute in incoming_attributes:
            if incoming_attribute in attribute_replacements:
                new_key = attribute_replacements[incoming_attribute]
                new_value = incoming_attributes[incoming_attribute]
                incoming_attributes[new_key] = new_value
                del(incoming_attributes[incoming_attribute])     
        
        self.attributes.update(incoming_attributes)
        self.string = ss.string
    
    #Make sentence also behave as a dictionary
    
    def get_vector(self, attribute_names, default_value='', replace_infinite=False, replace_nan=False):
        vector = []
        for name in attribute_names:
            try:
                attvalue = float(self.attributes[name])
                if replace_infinite:
                    attvalue = float(str(attvalue).replace("inf", "500"))
                if replace_nan:
                    attvalue = float(str(attvalue).replace("nan", "0"))
                vector.append(attvalue)
                log.debug("Adding attribute[{}]='{}'".format(name,attvalue))
            except KeyError:
                vector.append(default_value)
                log.debug("Adding fallback attribute[{}]='{}'".format(name,default_value))
        log.debug("Simple sentence returns vector: {}".format(vector))
        return vector
            
    def __getitem__(self, obj, cls=None): 
        return self.get_attribute(obj)

    def __setitem__(self, obj, val): 
        self.attributes[obj] = val

    def __delete__(self, obj): 
        del(self.attributes[obj])
        
    def __iter__(self):
        return self.attributes.iterkeys()
