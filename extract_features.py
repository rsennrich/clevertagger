#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright © 2011 University of Zürich
# Author: Rico Sennrich <sennrich@cl.uzh.ch>

from __future__ import unicode_literals
import sys
import os
import re
import socket
import time
import codecs
from subprocess import Popen, PIPE
from collections import defaultdict
from smor_getpos import get_true_pos
from config import SFST_BIN, SMOR_MODEL, PORT, SMOR_ENCODING

class MorphAnalyzer():
    """Base class for morphological analysis and feature extraction"""

    def __init__(self):
        
        self.posset = defaultdict(set)

        # Gertwol/SMOR only partially analyze punctuation. This adds missing analyses.
        for item in ['(',')','{','}','"',"'",u'”',u'“','[',']','«','»','-','‒','–','‘','’','/','...','--']:
            self.posset[item].add('$(')
        self.posset[','].add('$,')
        for item in ['.',':',';','!','?']:
            self.posset[item].add('$.')

        #regex to check if word is alphanumeric
        #we don't use str.isalnum() because we want to treat hyphenated words as alphanumeric
        self.alphnum = re.compile(r'^(?:\w|\d|-)+$', re.U)
        
        
    def create_features(self, line):
        """Create list of features for each word"""
        
        truth = ''
        pos = []
        linelist = line.split()
        
        if not linelist:
            return '\n'
        
        #feature: word itself
        word = linelist[0]
        
        #if input is already tagged, tag is added to end (for training / error analysis)
        if len(linelist) > 1:
            truth = linelist[1]
        
        #feature: is word uppercased?
        if word[0].isupper():
            feature_upper = 'uc'
        else:
            feature_upper = 'lc'

        #feature: is word alphanumeric?
        if self.alphnum.search(word[0]):
            feature_alnum = 'y'
        else:
            feature_alnum = 'n'

        #feature: list of possible part of speech tags
        if word in self.posset:
            pos = self.posset[word]
        for alternative in spelling_variations(word):
            if alternative in self.posset:
                pos = self.posset[alternative].union(pos)

        pos = sorted(pos)+['ZZZ']*10
        posstring = '\t'.join(pos[:10])

        outstring = ("{w}\t{wlower}\t{upper}\t{alnum}\t{pos}".format(w=word, wlower=word.lower(), upper=feature_upper, pos=posstring, alnum=feature_alnum))

        if truth:
            outstring += '\t'+truth
            
        return outstring+'\n'



class GertwolAnalyzer(MorphAnalyzer):

    def analyze(self, inlines):
        """Call Gertwol analysis"""

        new = []

        #prepare gertwol analysis
        for line in inlines:
            
            linelist = line.split()
            if not linelist:
                continue
            
            word = linelist[0]
            if not word in self.posset:
                self.posset[word] = set([])
                new.append(word)

                #deal with spelling variations that Gertwol doesn't know
                for alternative in spelling_variations(word):
                    if not alternative in self.posset:
                        self.posset[alternative] = set([])
                        new.append(alternative)

        if new:
            morph_tool = Popen([os.path.join(sys.path[0], 'gertwol-wrapper.py')], stdin=PIPE, stdout=PIPE)
            analyses = morph_tool.communicate('\n'.join(new)[0])
            self.convert(analyses)

    
    def convert(self, analyses):
        """Convert Gertwol output into list of POS tags"""
        
        word = ''
        pos = ''
        for line in analyses.split(b'\n'):

            line = line.decode("UTF-8")

            if line.startswith('"<'):
                word = line[2:-2]
                continue

            linelist = line.split()
            i = 1
            pos = ''
            while len(linelist) > i:
                if linelist[i] in ['*']: #information we throw away
                    i += 1
                        
                if linelist[i] in ['TRENNBAR', 'PART', 'V', 'NUM', 'A', 'pre', 'post', 'ABK']:
                    if pos:
                        pos += ':'
                    pos += linelist[i]
                    i += 1
                    
                elif linelist[i] in ['S'] and len(linelist) > i+1 and linelist[i+1] in ['EIGEN']:
                    pos += ':'.join(linelist[i:i+2])
                    i += 2
                    break
                    
                else:
                    if pos:
                        pos += ':'
                    pos += linelist[i]
                    i += 1
                    break
                    
            if 'zu' in linelist: # distinguish between "aufhören" and "aufzuhören"
                pos += ':'+'zu'
                
            elif pos.startswith('A:') and len(linelist) > i+1: #distinguish between ADJA and ADJD
                pos += ':'+'flekt'
                
            if pos:
                self.posset[word].add(pos)


    def main(self):
        """do morphological analysis/feature extraction batchwise"""
        buf = []
        for i, line in enumerate(sys.stdin):

            buf.append(line)
            
            if i and not i % 10000:
                self.analyze(buf)
                for line in buf:
                    sys.stdout.write(self.create_features(line))
                buf = []
                
        self.analyze(buf)
        for line in buf:
            sys.stdout.write(self.create_features(line))


class SMORAnalyzer(MorphAnalyzer):

    def __init__(self):
        MorphAnalyzer.__init__(self)

        #regex to get coarse POS tag from SMOR output
        self.re_mainclass = re.compile(r'<\+(.*?)>')
        self.PORT = PORT

        # start server, and make sure it accepts connection
        self.p_server = self.server()

    def server(self):
        """Start a socket server. If socket is busy, look for available socket"""

        while True:
            try:
                server = Popen([SFST_BIN, str(self.PORT), SMOR_MODEL], stderr=PIPE, bufsize=0)
            except OSError as e:
                if e.errno == 2:
                    sys.stderr.write('Error: {0} not found. Please install sfst and/or adjust SFST_BIN in clevertagger config.\n'.format(SFST_BIN))
                    sys.exit(1)
            error = b''
            while True:
                error += server.stderr.read(1)
                if error.endswith(b'listening to the socket ...'):
                    return server
                elif error.endswith(b'ERROR on binding'):
                    self.PORT += 1
                    sys.stderr.write('PORT {0} busy. Trying to use PORT {1}\n'.format(self.PORT-1, self.PORT))
                    break
                elif server.poll():
                    error += server.stderr.read()
                    error = error.decode('utf-8')
                    sys.stderr.write(error)
                    sys.exit(1)


    def client(self, words):
        """Communicate with socket server to obtain analysis of word list."""

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', self.PORT))
        s.sendall('\n'.join(words).encode(SMOR_ENCODING))
        s.shutdown(socket.SHUT_WR)
        analyses = b''
        data = True
        while data:
            data = s.recv(4096)
            analyses += data

        return analyses

    
    def convert(self, analyses):
        """convert SMOR output into list of POS tags"""
        
        word = ''
        for line in analyses.split(b'\n'):

            line = line.decode(SMOR_ENCODING)

            if line.startswith('>'):
                word = line[2:]
                continue

            if line.startswith('no result'):
                continue
           
            try:
                raw_pos = self.re_mainclass.search(line).group(1)
            except:
                continue
            
            pos, pos2 = get_true_pos(raw_pos, line)
                            
            if pos:
                self.posset[word].add(pos)
            if pos2:
                self.posset[word].add(pos2)


    def analyze(self, lines):
        """get all new words from input lines and send them to SMOR server for analysis"""

        todo = []
        for line in lines:

            linelist = line.split()
            if not linelist:
                continue

            word = linelist[0]
            if not word in self.posset:

                self.posset[word] = set([])
                todo.append(word)

                #deal with spelling variations that Gertwol doesn't know
                for alternative in spelling_variations(word):
                    if not alternative in self.posset:
                        self.posset[alternative] = set([])
                        todo.append(alternative)

        analyses = self.client(todo)
        self.convert(analyses)



    def main(self):
        """send lines in batches to SMOR server for analysis, and create output for each batch"""

        try:
            buf = []
            for i, line in enumerate(sys.stdin):
                buf.append(line)

                if i and not i % 10000:
                    self.analyze(buf)
                    for line in buf:
                        sys.stdout.write(self.create_features(line))
                    buf = []

            self.analyze(buf)
            for line in buf:
                sys.stdout.write(self.create_features(line))

        finally:
            self.p_server.terminate()


def spelling_variations(word):
    """Deal with spelling variations that morphology system may not know"""
            
    if word.startswith('Ae'):
        yield u"Ä" + word[2:]
    elif word.startswith(u'Oe'):
        yield u"Ö" + word[2:]
    elif word.startswith('Ue'):
        yield u"Ü" + word[2:]
        
    if "ss" in word:
        sharplist = word.split('ss')
        for i in range(len(sharplist)-1):
            yield sharplist[i]+u'ß'+sharplist[i+1]

    if u"ß" in word:
        sharplist = word.split(u'ß')
        for i in range(len(sharplist)-1):
            yield sharplist[i]+'ss'+sharplist[i+1]

    if "ae" in word:
        tmplist = word.split('ae')
        for i in range(len(tmplist)-1):
            yield tmplist[i]+u'ä'+tmplist[i+1]
        
    if "oe" in word:
        tmplist = word.split('oe')
        for i in range(len(tmplist)-1):
            yield tmplist[i]+u'ö'+tmplist[i+1]
        
    if "ue" in word:
        tmplist = word.split('ue')
        for i in range(len(tmplist)-1):
            yield tmplist[i]+u'ü'+tmplist[i+1]
   


if __name__ == '__main__':

    if sys.version_info < (3, 0):
        sys.stderr = codecs.getwriter('UTF-8')(sys.stderr)
        sys.stdout = codecs.getwriter('UTF-8')(sys.stdout)
        sys.stdin = codecs.getreader('UTF-8')(sys.stdin)

    Analyzer = SMORAnalyzer()
    #Analyzer = GertwolAnalyzer()

    Analyzer.main()
