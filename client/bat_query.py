
from __future__ import print_function
import redis
import argparse
import time
from nltk.translate.bleu_score import sentence_bleu, corpus_bleu

def candidates_from_file(file_name):
    """Retrieve tokens from txt file

    Args:
      file_name: Absolute file path

    Returns:
      A list of sentences and tokens
    """
    tokens = []
    queries = []
    with open(file_name, 'r') as f:
        for lines in f:
            # print(lines)
            queries.append(lines.split('\n')[0]) # get rid of '\n'
            token = lines.split(' ')
            if '\n' in token[-1]:
                token[-1] = token[-1][:-1] # remove '\n' in the end of sentence
            tokens.append(token)
    return queries, tokens

def references_from_file(file_name):
    """Retrieve tokens from txt file

    Args:
      file_name: Absolute file path

    Returns:
      A list of list of tokens
    """
    refers = []
    with open(file_name, 'r') as f:
        for lines in f:
            # print(lines)
            refer = lines.split(' ')
            if '\n' in refer[-1]:
                refer[-1] = refer[-1][:-1] # remove '\n' in the end of sentence
            refers.append([refer])
    return refers


def main():
  parser = argparse.ArgumentParser(description="Translation client example")
  parser.add_argument("--model_name", default="aver_ende",
                      help="model name")
  parser.add_argument("--host", default="localhost",
                      help="model server host")
  parser.add_argument("--tf_port", type=int, default=9000,
                      help="TensorFlow model server port")
  parser.add_argument("--redis_port", type=int, default=6379,
                      help="Redis model server port")
  parser.add_argument("--timeout", type=int, default=36000, # default to 10 hours
                      help="request timeout")
  parser.add_argument("--src", default="10-src-test.txt",
                      help="source text file path: ../data/???, default: 10-src-test.txt")
  parser.add_argument("--tgt", default="10-tgt-test.txt",
                      help="target text file path: ../data/???, default: 10-tgt-test.txt")
  args = parser.parse_args()

  redis_pool = redis.ConnectionPool(host=args.host, port=args.redis_port)
  redis_connect = redis.Redis(connection_pool=redis_pool)
  
  project_start_time = time.time()
  user = 'bat_'+str(redis_connect.incr('bat_user_id', 1))
  src_list_id = user + "_src" # e.g. "bat_1_src"
  tgt_list_id = user + "_tgt" # e.g. "bat_1_tgt"

  src_file = "../data/"+args.src
  tgt_file = "../data/"+args.tgt
  queries, batch_tokens = candidates_from_file(src_file)
  refer_tokens = references_from_file(tgt_file)
  print("# Data Loading: %.4f ms" % ((time.time()-project_start_time)*1000))

  query_start_time = time.time()
  # no caching read for batching but storing exists
  batch_size = len(queries)
  for query in queries:
    redis_connect.rpush(src_list_id, query) # push request to user's own list
    #: all data loaded, then wait for processing

  # append the user to the bat_user_list for help/serve
  redis_connect.rpush('bat_user_list', user)

  # results collection
  results = []
  for i in range(batch_size):
    result = redis_connect.blpop(tgt_list_id, args.timeout)
    latency = time.time() - query_start_time
    if result == None:
      results.append(' ') # timeout
    else:
      results.append(result[1])
    sentence_bleu_score = sentence_bleu(refer_tokens[i], results[i].split()) * 100
    print("\n==== SENTENCE: %6d ====\n" % i \
          + "{} \n=> {}\n::BLUE SCORE: ".format(queries[i], results[i]) \
          + "%.2f" % sentence_bleu_score \
          + "  Latency: %.2f" % latency)
    query_start_time = time.time()

  # after all the results are collected
  results_tokens = []
  for result in results:
    results_tokens.append(result.split())
  corpus_bleu_score = corpus_bleu(refer_tokens, results_tokens) * 100
  print("\n\n==== ENDS: %6d SENTENCES====" % batch_size)
  print("CORPUS BLEU SCORE: %.2f" % corpus_bleu_score + " for file: " + args.src)

if __name__ == "__main__":
        main()
