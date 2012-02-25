#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright © 2011 University of Zürich
# Author: Rico Sennrich <sennrich@cl.uzh.ch>
# Wrapper around old Gertwol version which uses/used latin1 encoding.

from subprocess import Popen, PIPE
import sys,os
from config import GERTWOL_BIN

input_latin1 = Popen(["iconv", "-c", "-f utf8", "-t latin1"], stdin=sys.stdin, stdout=PIPE)

gertwol = Popen([GERTWOL_BIN], stdin=input_latin1.stdout, stdout=PIPE)   

utf8 = Popen(["iconv", "-c", "-f latin1", "-t utf8"], stdin=gertwol.stdout, stdout=sys.stdout) 
utf8.wait()
