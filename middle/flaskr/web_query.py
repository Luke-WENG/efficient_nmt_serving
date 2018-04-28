
from __future__ import print_function
import redis

args_host = "localhost"
args_redis_port = 6379
args_timeout = 100
args_model_name = "aver_ende"

def web_query(query):
  # input: multiple-line sentences
  if len(query) > 0: # for non-empty inputs
    redis_pool = redis.ConnectionPool(host=args_host, port=args_redis_port)
    redis_connect = redis.Redis(connection_pool=redis_pool)

    user = 'web_'+str(redis_connect.incr('web_user_id', 1))
    redis_connect.rpush('web_user_list', user) # round-robin for all web users
    src_list_id = user + "_src" # e.g. "web_1_src"
    tgt_list_id = user + "_tgt" # e.g. "web_1_tgt"

    results = []
    tokens = query.split('\n')
    length_to_query = len(tokens)
    if length_to_query > 20:
      raise ValueError("Too much sentences in one query. Switch to batching processing")
      # TODO: batch processing
    # check the cache first
    for item in tokens:
      result = redis_connect.hget(item, args_model_name)
      if result == None:
        break
      else:
        results.append(result)
        tokens.remove(item)
        length_to_query = length_to_query - 1

    # if caching cannot solve the query
    if length_to_query > 0:
      for item in tokens:
        redis_connect.rpush(src_list_id, item)
      #: unfound data uploaded
      #: then block and wait for results

      #: To retrieve results from Redis
      #: r.rpush(user +'_tgt', "sentence1", "sentence2", "sentence3")
      for i in range(length_to_query):
        result = r.blpop(tgt_list_id, args_timeout)
        if result == None:
            # print "==Error:TimeOut=="
            results.append(" ")
        else:
            # print result[1]
            results.append(result[1]) # the str value

    output = '\n'.join(results)
    #: remove the first user named as var `user` from 'web_user_list'
    redis_connect.delete(src_list_id)
    redis_connect.delete(tgt_list_id)
    # redis_connect.lrem('web_user_list', user, 1)
    return output # multiple-line sentences    

  else:
    return "<Empty Input>"

