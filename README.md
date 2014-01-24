clevertagger - morphologically informed POS tagging for German
==============================================================

ABOUT
-----

clevertagger is a German part-of-speech tagger based on a CRF tool and SMOR.
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
- one of these CRF tools:
  - CRF++ http://crfpp.googlecode.com/svn/trunk/doc/index.html
  - Wapiti http://wapiti.limsi.fr/
- an SMOR transducer (e.g. Zmorge http://kitt.ifi.uzh.ch/kitt/zmorge/)
- SFST >= 1.3 http://www.ims.uni-stuttgart.de/projekte/gramotron/SOFTWARE/SFST.html

Optional dependencies:

- Perl (for tokenizer)

INSTALLATION INSTRUCTIONS
-------------------------

1. Install the dependencies listed above
2. Set the paths to the SMOR model and SFST in `config.py`, and set the CRF back-end.
3. You need a CRF++ or Wapiti model **(not included)**. For instructions on how to train your own, see below.


USAGE
-----

Assuming that you have trained a CRF++/Wapiti model, you can call clevertagger like this:

    ./clevertagger < input_file

Further options are displayed through

    ./clevertagger -h

By default, clevertagger expects tokenized input (one word per line; empty line for sentence boundaries);
for untokenized input, use the `--tokenize` option. A sentence splitter is included in `preprocessing`. To process raw text, call:

    preprocess/sentence_splitter < input_file | ./clevertagger --tokenize

clevertagger also supports the n-best-tagging features of CRF++/Wapiti.
Use the option `-n` to get multiple analyses for each sentence, and `-t` to get multiple analyses for each token.


TRAINING INSTRUCTIONS
---------------------

You need a training text in the format illustrated by `sample_training_file.txt`, 
i.e. one word per line, token and tag separated by spaces/tab; empty lines for sentence boundaries.

Then, execute the following two commands.
The second one may take you several days, depending on corpus size and the number of cores (set the number processes (-p) accordingly).

    ./clevertagger -e < training_file > crf_training_file

For CRF++, train a model like this (you may want to change some options, like the number of threads)

    crf_learn -f 3 -c 1.5 -p 10 crf_config crf_training_file crfmodel

For Wapiti, the command is this:

    wapiti train --compact -p crf_config --nthread 10 crf_training_file crfmodel

PERFORMANCE
-----------

Some evaluation results from (Sennrich, Volk and Schneider 2013), with TnT/clevertagger models trained on Tüba-D/Z (and the standard TreeTagger model), 
and using Morphisto for morphological analysis:

Tagging accuracy (in %)

<table>
  <tr>
    <th>Tagger</th>
    <th>TüBa-D/Z</th>
    <th>Sofies Welt</th>
  </tr>

  <tr>
    <td>TreeTagger</td>
    <td>94.9</td>
    <td>95.0</td>
  </tr>

  <tr>
    <td>TnT</td>
    <td>97.0</td>
    <td>94.7</td>
  </tr>

  <tr>
    <td>clevertagger</td>
    <td>97.6</td>
    <td>96.6</td>
  </tr>

</table>

Tagging performance depends on the quality of the morphological analysis, and is slightly better with the SMOR lexicon.

A more indirect evaluation measuring parsing performance of [ParZu](https://github.com/rsennrich/ParZu) on a 3000-sentence test set using different taggers:


<table>
  <tr>
    <th>Tagger</th>
    <th>precision</th>
    <th>recall</th>
    <th>f-measure</th>
  </tr>

  <tr>
    <td>TreeTagger</td>
    <td>85.6</td>
    <td>83.7</td>
    <td>84.6</td>
  </tr>

  <tr>
    <td>clevertagger</td>
    <td>87.9</td>
    <td>86.7</td>
    <td>87.3</td>
  </tr>

  <tr>
    <td>clevertagger (50-best)</td>
    <td>88.0</td>
    <td>87.7</td>
    <td>87.8</td>
  </tr>

  <tr>
    <td>gold tags</td>
    <td>89.8</td>
    <td>89.3</td>
    <td>89.5</td>
  </tr>

</table>


PUBLICATIONS
------------

The tagger is described in:

Rico Sennrich, Martin Volk and Gerold Schneider (2013):
   Exploiting Synergies Between Open Resources for German Dependency Parsing, POS-tagging, and Morphological Analysis.
   In: Proceedings of the International Conference Recent Advances in Natural Language Processing 2013, Hissar, Bulgaria.
