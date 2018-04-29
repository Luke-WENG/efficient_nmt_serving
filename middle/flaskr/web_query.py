
from __future__ import print_function
import redis

args_host = "localhost"
args_redis_port = 6379
args_timeout = 100
args_model_name = "aver_ende"

def web_query(query):
  # input: multiple-line sentences
  if len(query) > 0: # for non-empty inputs
    redis_pool = redis.ConnectionPool(host=args_host, port=args_redis_port, db=1) # for message queue
    red1 = redis.Redis(connection_pool=redis_pool)
    red0 = redis.Redis(host=args_host, port=args_redis_port, db=0) # for hash caching

    user = 'web_'+str(red1.incr('web_user_id', 1))
    src_list_id = user + "_src" # e.g. "web_1_src"
    tgt_list_id = user + "_tgt" # e.g. "web_1_tgt"

    results = []
    tokens = query.split('\r\n') # the '\r' here is important, otherwise the cache won't match.
    length_to_query = len(tokens)
    if length_to_query > 100:
      return "<Too much sentences in one query. Please switch to batching processing>"
      # TODO: batch processing
    # check the cache first
    tokens_for_loop = tokens[:]
    for item in tokens_for_loop:
      # print(str(length_to_query)+repr(item)) # this helps me to debug
      result = red0.hget(item, args_model_name)
      if result == None:
        # print(str(length_to_query))
        break
      else:
        results.append(result)
        tokens.remove(item)
        length_to_query = length_to_query - 1

    # if caching cannot solve the query
    if length_to_query > 0:
      for item in tokens:
        red1.rpush(src_list_id, item)
      #: unfound data uploaded
      #: then block and wait for results

      # append the user to the web_user_list for help/serve
      red1.rpush('web_user_list', user) # round-robin for all web users
      
      #: To retrieve results from Redis
      #: r.rpush(user +'_tgt', "sentence1", "sentence2", "sentence3")
      for i in range(length_to_query):
        result = red1.blpop(tgt_list_id, args_timeout)
        if result == None:
            # print "==Error:TimeOut=="
            waiting_in_queue = red1.lrem("web_user_list", 0, user) # check whether user is still in queue
            if waiting_in_queue:
              red1.rpush('timeout_user_list', user) # add to timeout_user_list, let web serving execute swiftly
              red1.set("timeout_exist", 1) # mark as timeout, let batch serving halt
              result = red1.blpop(tgt_list_id, 100000) # wait until results
            else: # already under processing
              result = red1.blpop(tgt_list_id, 100000) # wait until results
        results.append(result[1]) # the str value

    output = '\n'.join(results)
    #: remove the first user named as var `user` from 'web_user_list'
    red1.delete(src_list_id)
    red1.delete(tgt_list_id)
    # red1.lrem('web_user_list', user, 1)
    return output # multiple-line sentences    

  else:
    return "<Empty Input>"

