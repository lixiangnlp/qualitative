'''
Check overlap between two XML files originating from WMT
Created on Jul 12, 2016

@author: elav01
'''

import sys
from dataprocessor.ce.cejcml import CEJcmlReader

def check_overlap(bigfilename, smallfilename):
    bigfile = CEJcmlReader(bigfilename)
    smallfile = CEJcmlReader(smallfilename)
    small_ids = [p.get_safe_id_tuple() for p in smallfile]
    len_small_ids = len(small_ids)
    small_ids = set(small_ids)
    print "Sizes before and after summing ids", len_small_ids, len(small_ids)
    
    i = 0
    overlap = 0
    for parallelsentence in bigfile:
        i+=1 
        big_id = parallelsentence.get_safe_id_tuple()
        if big_id in small_ids:
            print big_id
            overlap += 1
    
    print "overall overlap: ", overlap, i         
    


if __name__ == '__main__':
    check_overlap(sys.argv[1], sys.argv[2])
