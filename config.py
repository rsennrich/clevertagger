# Path to compact morphisto model. You can download a pre-compiled morphisto model from http://code.google.com/p/morphisto
# to compact it, run:
# fst-compiler morphisto-02022011.a morphisto-02022011.compact.a
MORPHISTO_MODEL = '/home/rico/morphisto/morphisto-02022011.compact.a'

# Path to fst-infl2-daemon (SFST >= 1.3)
SFST_BIN = '/home/rico/Downloads/SFST146/src/fst-infl2-daemon'

# Used for fst-infl2-daemon (the Morphisto socket server).
HOST = 'localhost'    # The remote host
PORT = 9010         # The same port as used by the server

# Code for feature extraction with Gertwol is still included, but support is deprecated
GERTWOL_BIN = '/opt/bin/uis-gertwol'