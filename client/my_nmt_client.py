# my_nmt_client.py
"""Example of a translation client."""

from __future__ import print_function

import argparse

import tensorflow as tf
import time

from grpc.beta import implementations

from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2

from nltk.translate.bleu_score import sentence_bleu, corpus_bleu


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

def candidates_from_file(file_name):
	"""Retrieve tokens from txt file

	Args:
	  file_name: Absolute file path

	Returns:
	  A list of tokens
	"""
	tokens = []
	with open(file_name, 'r') as f:
		for lines in f:
			token = lines.split(' ')
			token[-1] = token[-1][:-1] # remove '\n' in the end of sentence
			tokens.append(token)
	return tokens

def references_from_file(file_name):
	"""Retrieve tokens from txt file

	Args:
	  file_name: Absolute file path

	Returns:
	  A list of list of tokens
	"""
	tokens = []
	with open(file_name, 'r') as f:
		for lines in f:
			token = lines.split(' ')
			token[-1] = token[-1][:-1] # remove '\n' in the end of sentence
			tokens.append([token])
	return tokens

def main():
  parser = argparse.ArgumentParser(description="Translation client example")
  parser.add_argument("--model_name", required=True,
                      help="model name")
  parser.add_argument("--host", default="localhost",
                      help="model server host")
  parser.add_argument("--port", type=int, default=9000,
                      help="model server port")
  parser.add_argument("--timeout", type=float, default=10.0,
                      help="request timeout")
  parser.add_argument("--src", default="10-src-test.txt",
                      help="source text file path: ../data/???, default: 10-src-test.txt")
  parser.add_argument("--tgt", default="10-tgt-test.txt",
                      help="target text file path: ../data/???, default: 10-tgt-test.txt")
  args = parser.parse_args()

  channel = implementations.insecure_channel(args.host, args.port)
  stub = prediction_service_pb2.beta_create_PredictionService_stub(channel)

  src_file = "../data/"+args.src
  batch_tokens = candidates_from_file(src_file)

  # batch_tokens = [
  #     ["Hello", "world", "!"],
  #     ["My", "name", "is", "John", "."],
  #     ["I", "live", "on", "the", "West", "coast", "."]]

  futures = []
  for tokens in batch_tokens:

    future = translate(stub, args.model_name, tokens, timeout=args.timeout)
    futures.append(future)

  results = []
  for tokens, future in zip(batch_tokens, futures):
    start_time = time.time()
    result = parse_translation_result(future.result())
    results.append(result)
    print("{} \n=> {}".format(" ".join(tokens), " ".join(result)))
    print("### Latency: %.4f ms" % ((time.time()-start_time)*1000))

  if args.tgt:
    tgt_file = "../data/"+args.tgt
    refer_tokens = references_from_file(tgt_file)
    corpus_bleu_value = corpus_bleu(refer_tokens, results) * 100
    print("Corpus Bleu Value: %f" % corpus_bleu_value)


if __name__ == "__main__":
  main()
