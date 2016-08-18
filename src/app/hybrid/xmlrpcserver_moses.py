from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from app.autoranking.application import Autoranking
from mt.hybrid import DummyTriangleTranslator
import sys
from app.hybrid.translate import SimpleTriangleTranslator
import argparse
from mt.moses import ProcessedMosesWorker

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)
    
parser = argparse.ArgumentParser(description='XML RPC server front for pre- and post-processing Moses SMT')
parser.add_argument('--host', help="Host name where XML RPC server will run")
parser.add_argument('--port', type=int, help="Port where XML RPC server will respond")
parser.add_argument('--uri', help="URI where Moses server responds")
parser.add_argument('--source_language', help="source language 2-letter code")
parser.add_argument('--target_language', help="target language 2-letter code")
parser.add_argument('--truecaser_model', help="filename of the truecasing model")
parser.add_argument('--splitter_model', default=None, help="filename of the compound splitting model")
args = parser.parse_args()

translator = ProcessedMosesWorker(uri=args.uri,
                                  source_language=args.source_language,
                                  target_language=args.target_language,
                                  truecaser_model=args.truecaser_model,
                                  splitter_model=args.splitter_model)
server = SimpleXMLRPCServer((args.host, args.port),
                            requestHandler=RequestHandler)
server.register_introspection_functions()

def process_task(params):
    text = params['text']
#    try:
    sys.stderr.write("Received task\n")
    translated_text, description = translator.translate(text)
    transaction_id = 0
    result = {
            "errorCode": 0, 
            "errorMessage": "OK",
            "translation": [
                {
                    "translated": [
                        {
                            "text": translated_text, 
                            "description": description,
                            "score": 0,
                        }
                    ], 
                }
            ], 
            "translationId": transaction_id
        }
    return result
#    except:
#        result = """{
#            "errorCode": 1, 
#            "errorMessage": "ERROR"
#            }"""
#        return result

server.register_function(process_task, 'process_task')
print "server ready"
server.serve_forever()
