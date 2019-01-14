#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright © 2011 University of Zürich
# Author: Rico Sennrich <sennrich@cl.uzh.ch>

from __future__ import unicode_literals

DESC = """clevertagger is a German part-of-speech tagger based on a linear-chain CRF and SMOR.
It requires tokenized and sentence-delimited input (one token per line, empty line between sentenes) in UTF-8 encoding."""

import sys
import os
import argparse
import pexpect
from subprocess import Popen, PIPE

import extract_features
from config import CRF_BACKEND, CRF_MODEL, CRF_BACKEND_EXEC

# root directory (for relative path resolution) if file is run as script
root_directory = sys.path[0]
# root directory (for relative path resolution) if file is loaded as a module
if '__file__' in globals():
    root_directory = os.path.dirname(os.path.abspath(__file__))

if not os.path.isabs(CRF_MODEL):
    CRF_MODEL = os.path.join(sys.path[0], CRF_MODEL)

def parse_command_line():
    parser = argparse.ArgumentParser(description=DESC)

    parser.add_argument('-e', action="store_true",
                    help='Feature extraction only (no tagging).')

    parser.add_argument('-i', '--input', type=argparse.FileType('r'),
                    default=sys.stdin, metavar='FILE',
                    help='Input file. If not given, stdin is used.')

    parser.add_argument('-m', '--model', type=str,
                    default=CRF_MODEL, metavar='FILE',
                    help='Path to CRF++/Wapiti model.')

    parser.add_argument('-n', '--nbestsents', type=int,
                    default=1, metavar='N',
                    help='Print N best analyses for each sentence.')

    parser.add_argument('-t', '--nbesttags', type=int,
                    default=1, metavar='N',
                    help='Print N best analyses for each token.')

    parser.add_argument('--tokenize', action="store_true",
                    help='Tokenize text before tagging.')

    return parser.parse_args()


def main(args):

    if args.nbesttags > 1 and args.nbestsents > 1:
        sys.stderr.write('ERROR: --nbesttags and --nbestsents are mutually exclusive options. Aborting.\n')
        exit()

    if args.nbesttags > 1 and CRF_BACKEND == 'wapiti':
        sys.stderr.write('ERROR: --nbesttags is only supported for CRF++. Aborting.\n')
        exit()

    if args.e:
        e_out = sys.stdout
    else:
        e_out = PIPE
    
    if args.tokenize:
        tokenizer = Popen(['perl', os.path.join(sys.path[0], 'preprocess', 'tokenizer.perl'), '-l', 'de'], stdout=PIPE, stdin=args.input)
        e_in = tokenizer.stdout
    else:
        e_in = args.input
    
    extract = Popen([os.path.join(sys.path[0], 'extract_features.py')], stdin=e_in, stdout=e_out)
    
    if args.e:
        extract.wait()

    else:

        if CRF_BACKEND == 'wapiti':
            cmd = [CRF_BACKEND_EXEC, 'label', '-m', args.model]
            if args.nbestsents > 1:
                cmd += ['-s', '-p', '-n', str(args.nbestsents)]
        elif CRF_BACKEND == 'crf++':
            cmd = [CRF_BACKEND_EXEC, '-m', args.model]
            if args.nbesttags > 1:
                cmd += ['-v', '2']
            elif args.nbestsents > 1:
                cmd += ['-n', str(args.nbestsents)]
        else:
            sys.stderr.write('Error: invalid value \'{0}\' for option \'CRF_BACKEND\'\n'.format(CRF_BACKEND))
            sys.exit(1)

        try:
            tagging = Popen(cmd, stdin=extract.stdout, stdout=PIPE, cwd = root_directory)
        except OSError as e:
            if e.errno == 2:
                sys.stderr.write('Error: Executable {0} not found. Please install {0} and/or adjust CRF_BACKEND_EXEC in the clevertagger config file.\n'.format(CRF_BACKEND_EXEC))
                sys.exit(1)
        postprocess = Popen(['python', os.path.join(sys.path[0], 'postprocess.py'), str(args.nbesttags)], stdin=tagging.stdout, stdout=sys.stdout)

        postprocess.wait()


class Clevertagger(object):
    """This class initializes a persistent object with the clevertagger model. It exposes one method tag() which can be called repeatedly.
    This currently only supports a subset of options (1-best tagging with Wapiti and tokenized input)

    usage example:

    import clevertagger
    tagger = clevertagger.Clevertagger()

    for sentence in tagger.tag(['Das ist ein Test .', 'Das auch .']):
        print sentence + '\n'
    """
    def __init__(self):

        try:
            self.smor = extract_features.SMORAnalyzer()
        except:
            self.smor = None
            raise

        if CRF_BACKEND == 'wapiti':
            tagger_args = ['label', '-m', CRF_MODEL]
            self.tagger = pexpect.spawn(CRF_BACKEND_EXEC, tagger_args, echo=False, encoding='utf-8')
            self.tagger.delaybeforesend = 0

            # get some initial output
            self.tagger.expect_exact('* Load model\r\n* Label sequences\r\n')
        else:
            sys.stderr.write('Error: unsupported value \'{0}\' for option \'CRF_BACKEND\'\n'.format(CRF_BACKEND))
            sys.exit(1)

    def tag(self, text):
        """tag some text. Input must be list of tokenized sentences."""

        text = [sentence.split() for sentence in text]

        # preprocessing: extract features from SMOR
        self.smor.analyze(set(word for sentence in text for word in sentence))

        preprocessed = []
        for sentence in text:
            words = []
            for word in sentence:
                words.append(self.smor.create_features(word))
            preprocessed.append(''.join(words))

        # main tagging step with wapiti
        sentences = process_by_sentence(self.tagger, preprocessed)

        # postprocessing: strip features and only keep input / tag
        sentences_out = []
        for sentence in sentences:
            sentence_out = []
            for line in sentence:
                items = line.split()
                word = items[0]
                tag = items[14]
                sentence_out.append(word + '\t' + tag)
            sentences_out.append('\n'.join(sentence_out))

        return sentences_out

    def __del__(self):

        if self.smor is not None:
            self.smor.p_server.terminate()

def process_by_sentence(processor, sentences):
    sentences_out = []
    for sentence in sentences:
        if not sentence:
            continue
        words = []
        processor.send(sentence + '\n')
        while True:
            word = processor.readline().strip()
            # hack for Wapiti stderr
            if word.endswith('sequences labeled'):
                continue
            elif word:
                words.append(word)
            else:
                break
        sentences_out.append(words)

    return sentences_out

if __name__ == '__main__':
    args = parse_command_line()
    main(args)
