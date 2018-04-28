
from __future__ import print_function

import argparse

import tensorflow as tf
import time
import redis

from grpc.beta import implementations

from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2

def parse_translation_result(result):
  """Parses a translation result.

  Args:
    result: A `PredictResponse` proto.

  Returns:
    A list of tokens.
  """
  lengths = tf.make_ndarray(result.outputs["length"])[0]
  hypotheses = tf.make_ndarray(result.outputs["tokens"])[0]

  # Only consider the first hypothesis (the best one).
  best_hypothesis = hypotheses[0]
  best_length = lengths[0]

  return best_hypothesis[0:best_length - 1] # Ignore </s>

def translate(stub, model_name, tokens, timeout=5.0):
  """Translates a sequence of tokens.

  Args:
    stub: The prediction service stub.
    model_name: The model to request.
    tokens: A list of tokens.
    timeout: Timeout after this many seconds.

  Returns:
    A future.
  """
  length = len(tokens)

  request = predict_pb2.PredictRequest()
  request.model_spec.name = model_name
  request.inputs["tokens"].CopyFrom(
      tf.make_tensor_proto([tokens], shape=(1, length)))
  request.inputs["length"].CopyFrom(
      tf.make_tensor_proto([length], shape=(1,)))

  return stub.Predict.future(request, timeout)

def web_query(query):
  # parser = argparse.ArgumentParser(description="Translation client example")
  # parser.add_argument("--model_name", required=True,
  #                     help="model name")
  # parser.add_argument("--host", default="localhost",
  #                     help="model server host")
  # parser.add_argument("--port", type=int, default=9000,
  #                     help="model server port")
  # parser.add_argument("--timeout", type=float, default=10.0,
  #                     help="request timeout")
  # parser.add_argument("--src", default="10-src-test.txt",
  #                     help="source text file path: ../data/???, default: 10-src-test.txt")
  # parser.add_argument("--tgt", default="10-tgt-test.txt",
  #                     help="target text file path: ../data/???, default: 10-tgt-test.txt, input 'None' or 'none' to stop")
  # args = parser.parse_args()
  args_model_name = "aver_ende"
  args_host = "localhost"
  args_TF_port= 9000
  args_Redis_port = 6379
  args_timeout = 100
  args_src = None
  args_tgt = None


  channel = implementations.insecure_channel(args_host, args_TF_port)
  stub = prediction_service_pb2.beta_create_PredictionService_stub(channel)


  # redis 
  redis_pool = redis.ConnectionPool(host=args_host, port=args_Redis_port)
  redis_connect = redis.Redis(connection_pool=redis_pool)

  batch_tokens = []
  for query_sentence in query.split('\n'):
    batch_tokens.append(query_sentence.split())

  # batch_tokens = [
  #     ["Hello", "world", "!"],
  #     ["My", "name", "is", "John", "."],
  #     ["I", "live", "on", "the", "West", "coast", "."]]

  project_start_time = time.time()
  futures = []
  for tokens in batch_tokens:
    future = translate(stub, args_model_name, tokens, timeout=args_timeout)
    futures.append(future)

  # Start Querying
  # print("# Initializing and Data Loading: %.4f ms" % ((time.time()-project_start_time)*1000))
  results_start_time = time.time()
  # results = []
  outputs = ""
  for tokens, future in zip(batch_tokens, futures):
    query_start_time = time.time()
    # query redis first
    redis_key_string = ''
    for item in tokens:
        redis_key_string = redis_key_string + item + ' '
    redis_result = redis_connect.hget(redis_key_string, args_model_name) # try to get redis's result first
    # Why not input str(tokens) as key?
    # Because unicode like \xe could become \\xe in str(), which is hard to recover later.
    if redis_result == None:
        result = parse_translation_result(future.result())
        # save the results into redis
        redis_val_string = ''
        for item in result:
            redis_val_string = redis_val_string + item + ' '
        redis_connect.hset(redis_key_string, args_model_name, redis_val_string) 
        redis_connect.expire(redis_key_string, 600) # key expires after 10 minutes
    else: # change string like , into list
        result = redis_result.split() # turn sentences into lists 
    # results.append(result)
    # print("{} \n=> {}".format(" ".join(tokens), " ".join(result)))
    output = " ".join(result)
    # print("### Latency: %.4f ms" % ((time.time()-query_start_time)*1000))
    query_latency = time.time()-query_start_time
    outputs = outputs + output + '\n'
  # print("\n# Total Latency: %.4f ms" % ((time.time()-results_start_time)*1000))
  total_latency = time.time()-results_start_time
  outputs = outputs[:-1] # remove the last \n
  return outputs


