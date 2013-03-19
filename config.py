# Path to compact SMOR model. You can download a pre-compiled SMOR model (with Morphisto lexicon) from http://code.google.com/p/morphisto
# to compact it, run:
# fst-compiler morphisto-02022011.a morphisto-02022011.compact.a
SMOR_MODEL = '/home/rico/morphisto/morphisto-02022011.compact.a'

# Morphisto uses UTF-8 encoding, SMOR with Stuttgart lexicon uses latin-1. Set accordingly.
# The clevertagger frontend always uses UTF-8 encoding for input/output, regardless of the encoding of the morphology tool.
SMOR_ENCODING = 'UTF-8'

# Path to fst-infl2-daemon (SFST >= 1.3)
SFST_BIN = 'fst-infl2-daemon'

# Used for fst-infl2-daemon (the socket server that provides the analyses).
PORT = 9010         # The default port; if busy, port will be incremented by 1 until available port is found

# Code for feature extraction with Gertwol is still included, but support is deprecated
GERTWOL_BIN = '/opt/bin/uis-gertwol'
