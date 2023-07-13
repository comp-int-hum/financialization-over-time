# Bring in libraries at the very top of your code.
import csv
import re
import logging
import random
import pickle
import json

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

# Minimum length of words, otherwise they are discarded.
minimum_characters = 3

# For each "group", we'll collect the number of times each topic
# occurs.
groupwise_topic_counts = {}

# Read in the model that was previously trained and serialized.
with open("topic_model.bin", "rb") as ifd:
    model = pickle.loads(ifd.read())

# Open your file to read ("r") in text mode ("t") as a variable 
# ("ifd" is what Tom uses when reading files, it stands for 
# "input file descriptor").
with open("Documents/CompHuman/karthik.tsv", "rt") as ifd:
    
    # Use the file handle to create a CSV file handle, specifying 
    # that the delimiter is actually <TAB> rather than <COMMA>.
    cifd = csv.DictReader(ifd, delimiter="\t")
    
    # Iterate over each row of your file: since we used DictReader 
    # above, each row will be a dictionary.
    for row in cifd:
        
        # This is where we decide which "group" this document belongs to.  Here, we'll take
        # the publication year and make it a bit more coarse-grained by rounding everything
        # to the nearest 10-year span.
        resolution = 5
        group_value = int(row["rights_date_used"])
        if group_value < 1200 or group_value > 2020:
            continue
        group = group_value - (group_value % resolution)
        
        # Make sure there is a bucket for the group.
        groupwise_topic_counts[group] = groupwise_topic_counts.get(group, {})
        
        # We want to prepare the data the same way we prepared the data that
        # trained the model (there may be situations where we'd do something
        # different, but only with a particularly good reason!).
        tokens = gpp.split_on_space(
            gpp.strip_short(
                gpp.remove_stopwords(
                    gpp.strip_non_alphanum(
                        row["full_content"].lower()
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
            
            # Turn the subdocument tokens into integers and count them, using the
            # trained model (so it employs the same mapping as it was trained with).
            subdocument_bow = model.id2word.doc2bow(subdocument_tokens)
            
            # It will be useful to have the "bag-of-words" counts as a dictionary, too.
            subdocument_bow_lookup = dict(subdocument_bow)
            
            # Apply the model to the subdocument, asking it to give the specific
            # assignments, i.e. which topic is responsible for each unique word.
            #
            # Note how an underscore ("_") can be used, here and in other situations,
            # when you *don't* want to assign something to a variable, because you
            # aren't going to need it.  This makes the code (and your intentions)
            # clear.
            _, labeled_subdocument, _ = model.get_document_topics(
                subdocument_bow,
                per_word_topics=True
            )
            
            # Add the topic counts for this subdocument to the appropriate group.
            for word_id, topics in labeled_subdocument:
                # Gensim insists on returning *lists* of topics in descending order of likelihood.  When
                # the list is empty, it means this word wasn't seen during training (I think!), so we skip
                # it.
                if len(topics) > 0:
                    
                    # Assume the likeliest topic.
                    topic = topics[0]
                    
                    # Add the number of times this word appeared in the subdocument to the topic's count for the group.
                    groupwise_topic_counts[group][topic] = groupwise_topic_counts[group].get(topic, 0) + subdocument_bow_lookup[word_id]

# Save the counts to a file in the "JSON" format.  The 'indent=4' argument makes it a lot easier
# for a human to read the resulting file directly.
with open("topic_model_counts.json", "wt") as ofd:
    ofd.write(json.dumps(groupwise_topic_counts, indent=4))