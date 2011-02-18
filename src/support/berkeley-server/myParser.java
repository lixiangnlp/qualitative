import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import edu.berkeley.nlp.PCFGLA.BerkeleyParser;
import edu.berkeley.nlp.PCFGLA.CoarseToFineMaxRuleParser;
import edu.berkeley.nlp.PCFGLA.CoarseToFineNBestParser;
import edu.berkeley.nlp.PCFGLA.Corpus;
import edu.berkeley.nlp.PCFGLA.Grammar;
import edu.berkeley.nlp.PCFGLA.Lexicon;
import edu.berkeley.nlp.PCFGLA.MultiThreadedParserWrapper;
import edu.berkeley.nlp.PCFGLA.OptionParser;
import edu.berkeley.nlp.PCFGLA.ParserData;
import edu.berkeley.nlp.PCFGLA.TreeAnnotations;
import edu.berkeley.nlp.PCFGLA.BerkeleyParser.Options;
import edu.berkeley.nlp.io.PTBLineLexer;
import edu.berkeley.nlp.syntax.Tree;
import edu.berkeley.nlp.util.Numberer;


public class myParser extends BerkeleyParser {

		PTBLineLexer tokenizer;
		Boolean tokenize;
		CoarseToFineMaxRuleParser parser;
		Options opts;
		int kbest;
		
		public myParser(){
					
			String inFileName = "/home/elav01/taraxu_tools/berkeleyParser/grammars/eng_sm6.gr";			
			ParserData pData = ParserData.Load(inFileName);
			Grammar grammar = pData.getGrammar();
		    Lexicon lexicon = pData.getLexicon();
		    Numberer.setNumberers(pData.getNumbs());
		    
		    kbest = 10;
		    //if (opts.chinese) Corpus.myTreebank = Corpus.TreeBankType.CHINESE;
		    double threshold = 1.0;
		    
		    
		    //kbest parser
		    parser = new CoarseToFineNBestParser(grammar, lexicon, kbest ,threshold,-1, false , false , false , false, false, false, true);
		    parser.binarization = pData.getBinarization();
		    tokenizer = new PTBLineLexer();
		    String line = "";
		    
		}
		
		
		public List<Map<String, String>> parse (String line){
			try {
				
				System.out.println ("parsing first string");
				
				List<String>  sentence = tokenizer.tokenizeLine(line);
						
				
				if (sentence.size()>=80) {  
	    			System.err.println("Skipping sentence with "+sentence.size()+" words since it is too long."); 
	    		}
				
				List<Tree<String>> parsedTrees = parser.getKBestConstrainedParses(sentence, null, kbest);

				
//				List<ScoredTree> scoredList = this.outputTrees(parsedTrees, parser);
//				
//				for ( ScoredTree item : scoredList ){
//					System.out.println(item.logLikelihood + ":" + item.confidence + ":\t" + item.tree );
//				}

				return this.outputTrees(parsedTrees, parser);
				
				
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
				return null;
			}
		}
		
		public Integer sum(String x, String y) {
			System.out.println (x + y);
		    return 1;
		 }
	
		 /**
		 * @param parsedTree
		 * @param outputData
		 * @param opts
		 * @return 
		 */
		private List<Map<String,String>> outputTrees(List<Tree<String>> parseTrees, CoarseToFineMaxRuleParser parser) {
			
			ArrayList<Map<String, String>> treeList = new ArrayList<Map<String,String>>();
			
			for (Tree<String> parsedTree : parseTrees){
				
				Map<String,String> scoredTree =  new HashMap<String,String>();
				//
				if (! parsedTree.getChildren().isEmpty() ){
					
					scoredTree.put("logLikelihood", Double.toString(parser.getLogLikelihood()) );
					
					parsedTree = TreeAnnotations.unAnnotateTree(parsedTree);
					scoredTree.put("confidence",   Double.toString(parser.getLogLikelihood(parsedTree)) );
					scoredTree.put("tree", parsedTree.getChildren().get(0)+" )");
								
				}
				treeList.add(scoredTree);
			}
			
			return treeList;
		}
	
		private class ScoredTree {
			
			private double logLikelihood;
			private double confidence;
			private String tree;
			
			public ScoredTree(){
				this.confidence = Double.NEGATIVE_INFINITY;
				this.logLikelihood = Double.NEGATIVE_INFINITY;
				this.tree = "(())\n";
					 
			}
			
		}
}


