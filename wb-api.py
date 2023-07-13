import requests  # Importing the 'requests' library for making HTTP requests
import math  # Importing the 'math' library for mathematical operations
import json  # Importing the 'json' library for JSON handling
import re  # Importing the 're' library for regular expressions

# Constant defining the maximum number of documents per page
MAX_DOCS_PER_PAGE = 1001

# List of queries to be executed
queries = ["https://search.worldbank.org/api/v2/wds?format=json&qterm=climate%20finance&strdate=1990-01-01&lang_exact=English&disclstat_exact=Disclosed&fl=txturl"]

# List to store the seen object IDs
object_ids_seen = []

# Open a file called "test_worldbank.json" in write text mode for output
with open("test_worldbank.json", "wt") as json_per_line_out:
    
    # Iterate over each query
    for query in queries:
        
        # Send an HTTP GET request to the query URL and get the response
        response = requests.get(query)
        
        # Parse the response JSON and store it in 'objs'
        objs = response.json()
        
        # Get the total number of documents from the response
        num_documents = objs["total"]
        
        # Calculate the number of pages required to retrieve all documents
        num_pages = math.ceil(float(num_documents) / MAX_DOCS_PER_PAGE)
        
        # Iterate over each page
        for i in range(0, num_pages):
            
            # Initialize a variable 'x' to 0
            x = 0
            
            # Construct the full query URL for the current page
            full_query = query + "&rows=" + str(MAX_DOCS_PER_PAGE) + "&os=" + str(i*MAX_DOCS_PER_PAGE)
            
            # Send an HTTP GET request to the full query URL and get the response
            response = requests.get(full_query)
            
            # Parse the response JSON and store it in 'objs'
            objs = response.json()
            
            # Check if there are any documents in the response
            if len(objs["documents"]) > 0:
                
                # Iterate over each document in the response
                for docname, document in objs["documents"].items():
                    
                    # Skip processing if the document is not a facet
                    if docname != "facets":
                        
                        # Check if the document ID has not been seen before and if it has a 'txturl'
                        if document["id"] not in object_ids_seen and document["txturl"]:
                            
                            # Print a message indicating that a task has been performed
                            print("did a thing!")
                            
                            # Print the value of 'x'
                            print(x)
                            
                            # Increment the value of 'x'
                            x = x + 1
                            
                            # Send an HTTP GET request to the 'txturl' of the document and get the response
                            response = requests.get(document["txturl"])
                            
                            # Store the full content of the document in the document itself
                            document["full_content"] = response.text
                            
                            # Check if the document's full content matches the regex pattern "climat.*financ.*"
                            if re.search(r"climate[\s\w]*(?:finance|investment|policy|fund)|green[\s\w]*(?:finance|investment|fund)|ESG|green bond|sustainable bond|sustainability bond", document["full_content"]):
                                
                            
                                # Add the document ID to the list of seen object IDs
                                object_ids_seen.append(document["id"])
                                
                                # Write the document as a JSON string to the output file, followed by a newline character
                                json_per_line_out.write(json.dumps(document) + "\n")
