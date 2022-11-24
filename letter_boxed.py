#!/usr/bin/env -S python3 -u
import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, wait
from itertools import chain
from multiprocessing import cpu_count
from time import time

import networkx as nx

def Timer(fn):
    from time import perf_counter
    def inner(*args, **kwargs):
        start = perf_counter()
        ret = fn(*args, **kwargs)
        return (perf_counter() - start), ret
    return inner

parser = argparse.ArgumentParser()
parser.add_argument('--words', default='/usr/share/dict/words')
parser.add_argument('--tasks', type=int, default=cpu_count())
parser.add_argument('set1')
parser.add_argument('set2')
parser.add_argument('set3')
parser.add_argument('set4')
parser.add_argument('max', type=int)
args = parser.parse_args()

letters = frozenset({*args.set1} | {*args.set2} | {*args.set3} | {*args.set4})
chains = dict()
for setn in [args.set1, args.set2, args.set3, args.set4]:
    for letter in [*setn]:
        chains[letter] = frozenset(letters - {*setn})

words = list()
starts = defaultdict(list)
ends = defaultdict(list)
G = nx.DiGraph()
with open(args.words, 'r') as words_fh:
    for word in words_fh:
        word = word.strip()
        # Check the basic criteria of a candidate word:
        #   1. Must be at least three letters
        #   2. Must only contain letters that are in the four sets
        if (word_len := len(word)) >= 3 and not ({*word} - letters):
            # Now see if the letters in sequence "round the square"
            for index, letter in enumerate(word):
                if (next_index := index + 1) < word_len:
                    if word[next_index] not in chains[letter]:
                        # On the same side
                        break
                else:
                    # Everything checks out
                    G.add_node(word)
                    words.append(word)
                    starts[word[0]].append(word)
                    ends[word[-1]].append(word)
                    for word_next in starts[word[-1]]:
                        G.add_edge(word, word_next)
                    for word_next in ends[word[0]]:
                        G.add_edge(word_next, word)

def find_pangram_paths(word, pos, total_words):
    print(f'>>> Search paths from {word} {pos}/{total_words}')
    pangrams = list()
    for y in words:
        for z in range(args.max):
            try:
                for path in nx.all_shortest_paths(G, word, y, z + 1):
                    leftovers = letters - frozenset(chain(*path))
                    if not leftovers:
                        pangrams.append(path)
            except Exception as exc:
                pass
    return pangrams

pangram_futures = dict()
with ProcessPoolExecutor(max_workers=args.tasks) as executor:
    for index, word in enumerate(words):
            pangram_futures[word] = executor.submit(
                find_pangram_paths,
                word,
                index + 1,
                len(words)
            )

for word in pangram_futures:
    result = pangram_futures[word].result()
    for pangram in result:
        pangram_path = ' '.join(pangram)
        print(f'<<< {pangram_path}')
