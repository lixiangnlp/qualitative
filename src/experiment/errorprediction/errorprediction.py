'''
Created on 17 Apr 2013

@author: Eleftherios Avramidis
'''

from io_utils.sax.saxjcml2orange import SaxJcml2Orange
import sys

meta_attributes = ['wer',
                    'hper' 
                    'rper',
                    'iHper',
                    'iRper',
                    'missErr',
                    'extErr',
                    'rLexErr',
                    'hLexErr',
                    'rRer',
                    'hRer',
                    'biHper',
                    'biRper',
                    'rbRer',
                    'hbRer',
                    'bmissErr',
                    'bextErr',
                    'rbLexErr',
                    'hbLexErr',
                    ]
        
desired_attributes = []


if __name__ == '__main__':
    
    class_name = "hLexErr"
    input_filename = sys.argv[1]
    output_file = "/tmp/orange.tab"
    orangeconvertor = SaxJcml2Orange(input_filename, 
                                     class_name, 
                                     desired_attributes, 
                                     meta_attributes, 
                                     output_file)
    
    table = Orange.data.Table(output_file)
    
    new_domain = Orange.data.Domain([a for a in table.domain.variables if a.name != class_name], table.domain[class_name])
    new_data = Orange.data.Table(new_domain, table)
    
    def print_best_100(ma):
        for m in ma[:100]:
            print "%5.3f %s" % (m[1], m[0])
    

    
    print 'Relief:\n'
    meas = Orange.feature.scoring.Relief(k=20, m=50)
    mr = [ (a.name, meas(a, new_data)) for a in new_data.domain.attributes]
    mr.sort(key=lambda x: -x[1]) #sort decreasingly by the score
    print_best_100(mr)
    
    print "InfoGain\n"
    
    meas = Orange.feature.scoring.InfoGain()
    mr = [ (a.name, meas(a, new_data)) for a in new_data.domain.attributes]
    mr.sort(key=lambda x: -x[1]) #sort decreasingly by the score
    print_best_100(mr)
