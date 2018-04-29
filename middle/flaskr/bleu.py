# -*- coding: utf-8 -*-
def my():
    from nltk.translate.bleu_score import sentence_bleu, corpus_bleu
    tokens = []
    with open('bleu_test_token.txt','r') as f:
        for lines in f:
            print(lines)
            token = lines.split(' ')
            if '\n' in token[-1]:
                token[-1] = token[-1][:-1] # remove '\n' in the end of sentence
            tokens.append(token)
    print(tokens)
    print(len(tokens))
    print("\n======================================\n")

    refers = []
    with open('bleu_test_refer.txt','r') as f:
        for lines in f:
            print(lines)
            refer = lines.split(' ')
            if '\n' in refer[-1]:
                refer[-1] = refer[-1][:-1] # remove '\n' in the end of sentence
            refers.append([refer])
    print(refers)
    print(len(tokens))
    print("\n======================================\n")

    counter = 0
    bleu_score_sum = 0
    for token, refer in zip(tokens, refers):
        print('\t' + str(len(refer[0])) + ' | ' + str(refer))
        print('\t' + str(len(token)) + ' | ' + str(token))
        sentence_bleu_value = sentence_bleu(refer, token) * 100
        bleu_score_sum += sentence_bleu_value
        print("sentence_bleu_value: " + str(sentence_bleu_value) + '\n')
        counter += 1
    print("bleu_score_average: "+str(bleu_score_sum/counter))
    corpus_bleu_value = corpus_bleu(refers, tokens) * 100
    print("blue_corpus_score: "+str(corpus_bleu_value))


def example():
    from nltk.translate.bleu_score import sentence_bleu, corpus_bleu
    hyp1 = ['It', 'is', 'a', 'guide', 'to', 'action', 'which',\
            'ensures', 'that', 'the', 'military', 'always',\
            'obeys', 'the', 'commands', 'of', 'the', 'party']
    ref1a = ['It', 'is', 'a', 'guide', 'to', 'action', 'that',\
            'ensures', 'that', 'the', 'military', 'will', 'forever',\
            'heed', 'Party', 'commands']
    ref1b = ['It', 'is', 'the', 'guiding', 'principle', 'which',\
            'guarantees', 'the', 'military', 'forces', 'always',\
            'being', 'under', 'the', 'command', 'of', 'the', 'Party']
    ref1c = ['It', 'is', 'the', 'practical', 'guide', 'for', 'the',\
            'army', 'always', 'to', 'heed', 'the', 'directions',\
            'of', 'the', 'party']
    hyp2 = ['he', 'read', 'the', 'book', 'because', 'he', 'was',\
            'interested', 'in', 'world', 'history']
    ref2a = ['he', 'was', 'interested', 'in', 'world', 'history',\
            'because', 'he', 'read', 'the', 'book']

    list_of_references = [[ref1a, ref1b, ref1c], [ref2a]]
    hypotheses = [hyp1, hyp2]
    print(corpus_bleu(list_of_references, hypotheses)) # doctest: +ELLIPSIS
    # 0.5920...

    score1 = sentence_bleu([ref1a, ref1b, ref1c], hyp1)
    score2 = sentence_bleu([ref2a], hyp2)
    print(score1)
    print(score2)
    print((score1 + score2) / 2) # doctest: +ELLIPSIS

# example()
my()