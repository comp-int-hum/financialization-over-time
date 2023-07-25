# Bring in libraries at the very top of your code.
import csv
import re
import logging
import random
import pickle
import json
import gzip

# You can pick out specific functions or classes if you want to refer
# to them directly in your code
from gensim.corpora.dictionary import Dictionary
from gensim.models.ldamodel import LdaModel

# You can import a (sub)module under an alias, to avoid
# having to type out a long name.
#
# Note: "module", "package", "library", "submodule"...
# these tend to be used more or less interchangeably.
# They are technically differences, but they aren't
# relevant for most situations.
import gensim.parsing.preprocessing as gpp


logging.basicConfig(level=logging.INFO)


# A silly default setting in the csv library needs to be changed 
# to handle larger fields.
csv.field_size_limit(1000000000)

# Pick the number of tokens to have in each subdocument.
subdocument_length = 200

# Pick how many "topics" we'll pretend exist.
num_topics = 10

# Pick the maximum number of subdocuments to use.
maximum_subdocuments = 10000

minimum_characters = 3

subdocuments = []

# Open your file to read ("r") in text mode ("t") as a variable 
# ("ifd" is what Tom uses when reading files, it stands for 
# "input file descriptor").
### open json file here
with gzip.open("medium_worldbank.jsonl.gz", "rt") as ifd:
    
    # Use the file handle to create a CSV file handle, specifying 
    # that the delimiter is actually <TAB> rather than <COMMA>.
    
    #cifd = csv.DictReader(ifd, delimiter="\t")
    
    # Iterate over each row of your file: since we used DictReader 
    # above, each row will be a dictionary.
    for line in ifd: 
        row = json.loads(line)
        # for row in cifd:
        
        ### use the function json.loads which takes a string and returns a dictionary
        # Before, we simply split the full content on whitespace.
        #
        # Here, we'll also convert to lowercase, and use a few 
        # GenSim functions to remove very short words, stopwords,
        # and non-alphanumeric characters (e.g. punctuation).
        tokens = gpp.split_on_space(
            gpp.strip_short(
                gpp.remove_stopwords(
                    gpp.strip_non_alphanum(
                        row["content"].lower()
                    ),
                ),
            minsize=minimum_characters
            )
        )
                
        # Calculate, based on how many tokens are in the document 
        # and the desired subdocument length, how many subdocuments 
        # you'll be creating from this document.
        num_subdocuments = int(len(tokens) / subdocument_length)
        
        # The subdocuments don't exist yet, but you know how many there will be, so 
        # iterate over the subdocument number (i.e. 0, 1, 2 ... /num_subdocuments/).
        # So, in this loop, you're constructing the subdocument number /subnum/.
        for subnum in range(num_subdocuments):
            
            # Each subdocument has /subdocument_length/ tokens, and you are 
            # on subdocument number /subnum/, so it will start with token 
            # number /subnum/ * /subdocument_length/.
            start_token_index = subnum * subdocument_length
            
            # An easy way to know where this subdocument will end: the start of 
            # the next subdocument!
            end_token_index = (subnum + 1) * subdocument_length
            
            # You now know where this subdocument starts and ends, so "slice" out 
            # the corresponding tokens.
            subdocument_tokens = tokens[start_token_index:end_token_index]
            
            subdocuments.append(subdocument_tokens)

# Randomly shuffle the list of subdocuments so we get a nice sampling of all the
# different material in the dataset.
random.shuffle(subdocuments)

# Only use up to /maximum_subdocuments/ for our model.
subdocuments = subdocuments[0:maximum_subdocuments]

# Much like the /LabelEncoder/ and /CountVectorizer/ from last week, a GenSim 
# /Dictionary/ (not to be confused with a standard Python dictionary /{}/) will
# assign a unique integer to each word.
dct = Dictionary(documents=subdocuments)

# The /Dictionary/ also gathers total word-counts so we can filter based on how
# "interesting" they seem.  Here, we only keep words that occur at least 20 times
# in the entire dataset, and in no more than 50% of the subdocuments.
dct.filter_extremes(no_below=20, no_above=0.5)

# This unfortunate little statement is to "force" the /Dictionary/ to actually do
# its job!
temp = dct[0]

# The /Dictionary/ can now be used to transform each subdocument into word-counts
# (a row from the matrix in the lecture slides).
train = [dct.doc2bow(subdoc) for subdoc in subdocuments]

# We can now train the topic model.
model = LdaModel(
    train, 
    num_topics=num_topics, 
    id2word=dct, 
    alpha="auto", 
    eta="auto", 
    iterations=20, 
    passes=50, 
    eval_every=None, 
    chunksize=2000
)

# Save the trained model (note the "wb" and "ofd": we're writing binary output).
with open("topic_model.bin", "wb") as ofd:
    ofd.write(pickle.dumps(model))
