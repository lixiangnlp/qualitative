#!/usr/bin/python
# -*- coding: utf-8 -*-


'''
Created on 15 Οκτ 2010

@author: elav01
'''

from io.input.xmlreader import XmlReader
from io.input.orangereader import OrangeData
from classifier.bayes import Bayes
from classifier.tree import TreeLearner

if __name__ == '__main__':
    
    filename = "/home/elav01/workspace/TaraXUscripts/data/evaluations_feat.jcml"
    class_name = "rank"
    desired_attributes = []
    
    #Load data from external file
    pdr = XmlReader(filename) 
    dataset =  pdr.get_dataset()
    
    #convert data in orange format
    orangedata = OrangeData( dataset, class_name, desired_attributes )
    
    #split data the orange way (stratified)
    [training_part, test_part] = orangedata.split_data(0.1)
    training_data = OrangeData(training_part, class_name)
    test_data = OrangeData(test_part, class_name)
    
    
    orangedata.cross_validation()
    orangedata.print_statistics()
    
    #train data
    bayes = Bayes( training_data )
    tree = TreeLearner( training_data )
    svm = training_data.get_SVM()
    
    bayes.name = "bayes"
    tree.name = "tree"
    svm.name = "SVM"
    classifiers = [bayes, tree, svm]
    
    # compute accuracies
    acc = test_data.get_accuracy(classifiers)
    print "Classification accuracies:"
    for i in range(len(classifiers)):
        print classifiers[i].name, "\t", acc[i]