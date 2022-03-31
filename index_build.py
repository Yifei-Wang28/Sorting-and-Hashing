# Inf2-IADS Coursework 1, October 2019, revised October 2021
# Python source file: index_build.py
# Author: John Longley

# PART A: INDEXING A LARGE SET OF PLAINTEXT FILES
# (template file)


from buffered_io import *

# Global variables:

CorpusFiles = {'CAW': 'Carroll_Alice_in_Wonderland.txt',
               'OEL': 'Olaudah_Equiano_Life.txt',
               'SLC': 'Shudraka_Little_Clay_Cart.txt',
               'SCW' : 'Shakespeare_Complete_Works.txt',
               'TWP' : 'Tolstoy_War_and_Peace.txt'
               }
# :each file must be identified by a three-letter code
# :note that the files SCW and TCP are much larger than CAW, OEL, SLC

IndexFile = 'index.txt'
# :name of main index file to be generated

MetaIndex = {'': 0}
# :dictionary to be populated
# :MetaIndex[k] will give line number in IndexFile for key k

MetaIndexOp = (lambda s: 0)


# Initial scan to determine number of lines in a given text file:

def getNumberOfLines(filename):
    reader = BufferedInput(filename, 0.8)
    lines = 0
    chunk = reader.readchunk()
    while chunk != []:
        lines += len(chunk)
        chunk = reader.readchunk()
    reader.close()
    return lines


# Extracting list of words present in a single text line:

def getWords(s):
    t = s  # :could do some translation here to process accented symbols etc.
    words, flg = [], False
    for i in range(len(t)):
        if not flg:
            if t[i].isalpha():
                # potential start of word
                flg = True
                j = i
        else:
            if not t[i].isalpha():
                # potential end of word
                flg = False
                # design decision: ignore words of length < 4:
                if i - j >= 4:
                    words.append(t[j:i].casefold())
        # :assumes some terminator like \n is present
    return words


# Generation of unsorted index entries for a given textfile:

import math


def generateIndexEntries(filename, filecode, writer):
    numberOfLines = getNumberOfLines(filename)
    digits = int(math.log10(numberOfLines)) + 1
    padCtrl = '0' + str(digits)  # :controls leading zero padding
    reader = BufferedInput(filename, 0.2)
    currline = reader.readln()
    inlineNo = 1
    outlineNo = 0
    while currline != None:
        # process currline:
        words = getWords(currline)
        for w in words:
            writer.writeln(w + ':' + filecode + format(inlineNo, padCtrl) + '\n')
        outlineNo += len(words)
        # next line:
        inlineNo += 1
        currline = reader.readln()
    reader.close()
    return outlineNo  # :for testing


def generateAllIndexEntries(entryfile):
    global CorpusFiles
    writer = BufferedOutput(entryfile, 0.7)
    outlines = 0
    for filecode in CorpusFiles:
        outlines += generateIndexEntries(CorpusFiles[filecode], filecode, writer)
    writer.flush()
    return outlines


# Sorting the index entries:

import os


def splitIntoSortedChunks(entryfile):
    reader = BufferedInput(entryfile, 0.3)
    blockNo = 0
    chunk = reader.readchunk()
    while chunk != []:
        chunk.sort()
        blockfile = open('temp_' + str(blockNo) + '_' + str(blockNo + 1), 'w',
                         encoding='utf-8')
        # :output file written all at once, so no need for buffering here
        blockfile.writelines(chunk)
        blockfile.close()
        blockNo += 1
        chunk = reader.readchunk()
    reader.close()
    return blockNo


# TODO:
def mergeFiles(a, b, c):
    # Open the two files
    reader = BufferedInput('temp_{}_{}'.format(a, b), 0.3)
    reader1 = BufferedInput('temp_{}_{}'.format(b, c), 0.3)
    # create the output file
    writer = BufferedOutput('temp_{}_{}'.format(a, c), 0.3)
    # Read first lines for each file
    x = reader.readln()
    y = reader1.readln()
    while x or y:
        # Basically Merge sort: write the smaller one in,
        # and the index increments
        if x is None:
            writer.writeln(y)
            y = reader1.readln()
        elif y is None:
            writer.writeln(x)
            x = reader.readln()
        if x < y:
            writer.writeln(x)
            x = reader.readln()
        else:
            writer.writeln(y)
            y = reader1.readln()
    # close files after using
    reader.close()
    reader1.close()
    writer.flush()
    # delete the input files after merging
    os.remove('temp_{}_{}'.format(a, b))
    os.remove('temp_{}_{}'.format(b, c))
    # return the name of the output file


def mergeFilesInRange(a, c):
    # the three base cases:
    if c - a == 0:
        return None
    elif c - a == 1:
        return 'temp_{}_{}'.format(a, c)
    elif c - a == 2:
        mergeFiles(a, a+1, c)
        return 'temp_{}_{}'.format(a, c)
    # we first split the task into 2 subtasks
    p = (a + c) // 2

    # recursive call
    mergeFilesInRange(a, p)

    mergeFilesInRange(p, c)

    mergeFiles(a, p, c)
    return 'temp_{}_{}'.format(a, c)


# Putting it all together:


def sortRawEntries(entryfile):
    chunks = splitIntoSortedChunks(entryfile)
    outfile = mergeFilesInRange(0, chunks)
    return outfile


# Now compile the index file itself, 'compressing' the entry for each key
# into a single line:

def createIndexFromEntries(entryfile, indexfile):
    reader = BufferedInput(entryfile, 0.4)
    writer = BufferedOutput(indexfile, 0.4)
    inl = reader.readln()
    currKey, currDoc, lineBuffer = '', '', ''
    while inl != None:
        # get keyword and ref, start ref list:
        colon = inl.index(':')
        key = inl[:colon]
        doc = inl[colon + 1:colon + 4]  # :three-letter doc identifiers
        j = colon + 4
        while inl[j] == '0':
            j += 1
        line = inl[j:-1]
        if key != currKey:
            # new key: start a new line in index
            if key < currKey:
                print('*** ' + key + ' out of order.\n')
            if lineBuffer != '':
                writer.writeln(lineBuffer + '\n')
            currKey = key
            currDoc = ''
            lineBuffer = key + ':'
        if currDoc == '':
            # first doc for this key entry
            currDoc = doc
            lineBuffer = lineBuffer + doc + line
        elif doc != currDoc:
            # new doc within this key entry
            currDoc = doc
            lineBuffer = lineBuffer + ',' + doc + line
        else:
            lineBuffer = lineBuffer + ',' + line
        inl = reader.readln()
    # write last line and clean up:
    writer.writeln(lineBuffer + '\n')
    writer.flush()
    reader.close()


# Generating the meta-index for the index as a Python dictionary:

def generateMetaIndex(indexFile):
    global MetaIndex, MetaIndexOp
    MetaIndex.clear()
    reader = BufferedInput(indexFile, 0.9)
    indexline = 1
    inl = reader.readln()
    while inl != None:
        key = inl[:inl.index(':')]
        MetaIndex[key] = indexline
        indexline += 1
        inl = reader.readln()
    reader.close()
    MetaIndexOp = (lambda s: MetaIndex[s])


def buildIndex():
    rawEntryFile = 'raw_entries'
    entries = generateAllIndexEntries(rawEntryFile)
    sortedEntryFile = sortRawEntries(rawEntryFile)
    global IndexFile
    createIndexFromEntries(sortedEntryFile, IndexFile)
    generateMetaIndex(IndexFile)
    os.remove(rawEntryFile)
    os.remove(sortedEntryFile)
    print('Success! ' + str(len(MetaIndex)) + ' keys, ' +
          str(entries) + ' entries.')


# Accessing the index using 'linecache' (random access to text files by line):

import linecache


def indexEntryFor(key):
    global IndexFile, MetaIndex, MetaIndexOp
    try:
        lineNo = MetaIndexOp(key)  # :allows for other meta-indexing schemes
        indexLine = linecache.getline(IndexFile, lineNo)
    except KeyError:
        return None
    colon = indexLine.index(':')
    if indexLine[:colon] == key:
        return indexLine[colon + 1:]
    else:
        raise Exception('Wrong key in index line.')


# End of file
# import time
# time_start=time.time()
# buildIndex()
# time_end=time.time()
# print('totally cost',time_end-time_start)

generateAllIndexEntries('raw_entries')
splitIntoSortedChunks('raw_entries')
buildIndex()