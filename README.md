clevertagger - morphologically informed POS tagging for German
==============================================================

ABOUT
-----

clevertagger is a German part-of-speech tagger based on CRF++ and SMOR.
Its main component is a module that extracts features from SMOR's morphological analysis.
The combination of machine learning and FST-based morphological features promises a robust performance even for words that have not been observed during training,
in particular morphologically complex (and rare) adjectives, verbs and nouns, which tend to have high error rates with conventional taggers.

**The repository contains no pre-trained models!**
If you know of a German corpus that is annotated in the STTS tagset and has a permissive license, please let me know.

`smor_getpos.py` can also be used as a stand-alone script to convert the SMOR output into a list of possible part-of-speech tags in the STTS tagset.

AUTHOR
------

Rico Sennrich, Institute of Computational Linguistics, University of Zurich (http://www.cl.uzh.ch).


LICENSE
-------

clevertagger is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License (see LICENSE).

`tokenizer.perl` and `nonbreaking_prefix.de` are from the Moses toolkit and licensed under the LGPL (http://www.statmt.org/moses/)

`preprocessing/sentence_splitter` is from the NLTK and licensed under the Apache License 2.0 (https://github.com/nltk/nltk)


REQUIREMENTS
------------

- Linux (currently SFST is Unix/Linux only)
- Python >= 2.6
- CRF++ http://crfpp.googlecode.com/svn/trunk/doc/index.html
- an SMOR transducer (e.g. Morphisto http://code.google.com/p/morphisto/ )
- SFST >= 1.3 http://www.ims.uni-stuttgart.de/projekte/gramotron/SOFTWARE/SFST.html

Optional dependencies:

- Perl (for tokenizer)

INSTALLATION INSTRUCTIONS
-------------------------

1. Install the dependencies listed above
2. You can download a pre-compiled Morphisto build (e.g. morphisto-02022011.a), but it needs to be in fst-infl2 format.
to compile it, run:
    `fst-compiler morphisto-02022011.a morphisto-02022011.compact.a`
3. Set the paths to the Morphisto model and SFST in `config.py`
4. You need a CRF++ model **(not included)**. For instructions on how to train your own, see below.


USAGE
-----

Assuming that you have trained a CRF++ model, you can call clevertagger like this:

    ./clevertagger < input_file

Further options are displayed through

    ./clevertagger -h

By default, clevertagger expects tokenized input (one word per line; empty line for sentence boundaries);
for untokenized input, use the `--tokenize` option. A sentence splitter is included in `preprocessing`. To process raw text, call:

    preprocess/sentence_splitter < input_file | ./clevertagger --tokenize

clevertagger also supports the n-best-tagging features of CRF++.
Use the option `-n` to get multiple analyses for each sentence, and `-t` to get multiple analyses for each token.


TRAINING INSTRUCTIONS
---------------------

You need a training text in the format illustrated by `sample_training_file.txt`, 
i.e. one word per line, token and tag separated by spaces/tab; empty lines for sentence boundaries.

Then, execute the following two commands.
The second one may take you several days, depending on corpus size and the number of cores (set the number processes (-p) accordingly).

    ./clevertagger -e < training_file > crf_training_file

    crf_learn -f 3 -c 1.5 -p 10 crf_config crf_training_file crfmodel


PERFORMANCE
-----------

Some older evaluation results on Smultron 1.1, with TnT/clevertagger models trained on Tüba-D/Z (and the standard TreeTagger model), 
and using Gertwol (a proprietary morphological analyzer):

Error rates (in %)

<table>
  <tr>
    <th>Tagger</th>
    <th>Sofies Welt</th>
    <th>Economy Texts</th>
    <th>Economy Texts (simplified)*</th>
  </tr>

  <tr>
    <td>TreeTagger</td>
    <td>5.47</td>
    <td>8.75</td>
    <td>2.68</td>
  </tr>

  <tr>
    <td>TnT</td>
    <td>5.49</td>
    <td>5.95</td>
    <td>2.65</td>
  </tr>

  <tr>
    <td>clevertagger</td>
    <td>4.27</td>
    <td>7.05</td>
    <td>2.22</td>
  </tr>

</table>

*simplified means that the distinction between NE/NN/FM is ignored

Performance with Morphisto is slightly worse than that with Gertwol at the moment.
Tagging performance partially depends on the continued development of Morphisto;
if a word is unknown to the morphological analyzer, it may still be tagged correctly based on other features (the word itself, its context, whether it is uppercased etc.)
However, there is a strong bias towards tagging unknown words as NE (named entity),
since typically, most tokens in a typical training text that are unknown to a morphological analyzer are names.

With this caveat, here are three reasons to like clevertagger:

- Other taggers also behave poorly for unknown words, e.g. tagging all uppercased unknown words as nouns, even if they are sentence-initial verbs/adjectives.
  However, a FST-based morphology can cover a much bigger vocabulary, and thus have fewer unknown words.
- Performance of the tagger will probably improve further along with that of the morphological resources used (Morphisto or another lexicon based on the SMOR morphology).
- n-best-tagging can be beneficial in some applications, as the next evaluation shows.


A more indirect evaluation measuring parsing performance of [ParZu](https://github.com/rsennrich/ParZu) on a 1000-sentence test set using different taggers:


<table>
  <tr>
    <th>Tagger</th>
    <th>precision</th>
    <th>recall</th>
    <th>f-measure</th>
    <th>time</th>
  </tr>

  <tr>
    <td>TreeTagger</td>
    <td>87.04</td>
    <td>83.71</td>
    <td>85.34</td>
    <td>25s</td>
  </tr>

  <tr>
    <td>clevertagger</td>
    <td>88.08</td>
    <td>85.56</td>
    <td>86.80</td>
    <td>29s</td>
  </tr>

  <tr>
    <td>clevertagger (5-best)</td>
    <td>87.70</td>
    <td>86.61</td>
    <td>87.15</td>
    <td>93s</td>
  </tr>

  <tr>
    <td>clevertagger (50-best)</td>
    <td>87.41</td>
    <td>86.78</td>
    <td>87.09</td>
    <td>262s</td>
  </tr>

  <tr>
    <td>gold tags</td>
    <td>90.25</td>
    <td>88.49</td>
    <td>89.36</td>
    <td>27s</td>
  </tr>

</table>
