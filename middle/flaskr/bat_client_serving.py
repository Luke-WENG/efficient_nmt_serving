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


def check_timeout():
    patience = 10
    while red1.get("timeout_exist"):
        print("Timeout exists. Halting for 10 sec")
        patience -= 1
        time.sleep(10)
        if patience <= 0:
            break


def bat_client_serving():
    #: batch_size: process cycle for each batch user
    args_batch_size = 50
    args_model_name = "aver_ende"
    args_host = "localhost"
    args_tf_port= 9000
    args_redis_port = 6379
    args_timeout = 36000
    args_src = None
    args_tgt = None
    # Redis
    red0 = redis.Redis(host=args_host, port=args_redis_port, db=0) # for hash caching
    red1 = redis.Redis(host=args_host, port=args_redis_port, db=1) # for message queue
    # TensorFlow Serving
    channel = implementations.insecure_channel(args_host, args_tf_port)
    stub = prediction_service_pb2.beta_create_PredictionService_stub(channel)
    # Looping User Serving
    while True:
        try:
            print("Waiting for new users ...")
            user_to_serve = red1.blpop('bat_user_list')[1] # pick the first user, if none then wait
            print("Serving: "+user_to_serve)
            src_list_id = user_to_serve + "_src" # e.g. "bat_1_src"
            tgt_list_id = user_to_serve + "_tgt" # e.g. "bat_1_tgt"

            #: retrieve all queries of this user
            queries = red1.lrange(src_list_id, 0, args_batch_size-1) # pop args_batch_size queries
            red1.ltrim(src_list_id, args_batch_size, -1) # then remove them
            one_more_to_check = red1.lpop(src_list_id)
            if one_more_to_check == None:
                print("\n\n====== Aha! Batch user: " + user_to_serve + " is satisfied. :)")
                pass # this user is done. 
            else:
                red1.lpush(src_list_id, one_more_to_check) # put it back :)
                red1.rpush('bat_user_list', user_to_serve) # add user to the tail of queue

            #: try caching first
            length_of_queries = len(queries)
            queries_for_loop = queries[:]
            for item in queries_for_loop:
                # print(str(length_of_queries)+repr(item))
                result = red0.hget(item, args_model_name)
                if result == None:
                    # print(str(length_of_queries))
                    break
                    # no hope, go to TensorFlow Serving :(
                else:
                    red1.rpush(tgt_list_id, result) # for users to retrieve from list
                    queries.remove(item)
                    length_of_queries = length_of_queries - 1

            if length_of_queries > 0:
                batch_tokens = []
                for query in queries:
                    batch_token = [str(item) for item in query.split()]
                    batch_tokens.append(batch_token)
                    # red1.rpush(tgt_list_id, str(batch_token)) # too good to be true :)
                
                # batch_tokens = [
                #     ["Hello", "world", "!"],
                #     ["My", "name", "is", "John", "."],
                #     ["I", "live", "on", "the", "West", "coast", "."]]

                #: ready for TensorFlow Serving
                tf_start_time = time.time()
                futures = []
                for tokens in batch_tokens:
                    if 0 == len(tokens):
                        continue
                    future = translate(stub, args_model_name, tokens, timeout=args_timeout)
                    futures.append(future)

                translate_index = 0
                for tokens, future in zip(batch_tokens, futures):   
                    check_timeout()
                    result_tokens = parse_translation_result(future.result())
                    #: get results from tensorflow serving
                    #: result_tokens = ["Hallo", "Welt", "!"]
                    query = ' '.join(tokens)
                    result = ' '.join(result_tokens)
                    red0.hset(query, args_model_name, result) # cache result
                    red0.expire(query, 1200) # key expires after 20 minutes
                    red1.rpush(tgt_list_id, result) # return to users
                    print(tgt_list_id + ' ' + str(translate_index) \
                          + ' || ' + result[0] + "... || Latency: " \
                          + str(time.time() - tf_start_time))
                    translate_index += 1
            print("Well served: "+user_to_serve)
        except:
            red1.lpush('bat_user_list', user_to_serve)
            print("Fail to serve: "+user_to_serve)



        # result = " ".join(result_tokens)
        # red1.rpush(tgt_list_id, result) # for users to retrieve from list

bat_client_serving()