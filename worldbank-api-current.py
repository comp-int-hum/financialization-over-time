import requests
import math
import json
import re


MAX_DOCS_PER_PAGE = 1001
queries = ["https://search.worldbank.org/api/v2/wds?format=json&qterm=climate%20finance&strdate=1990-01-01&lang_exact=English&disclstat_exact=Disclosed&fl=txturl"
           "https://search.worldbank.org/api/v2/wds?format=json&qterm=mobilizing%20private%20finance&keyword_select=exactphrase&strdate=1990-01-01&lang_exact=English&disclstat_exact=Disclosed&fl=txturl"
           "https://search.worldbank.org/api/v2/wds?format=json&qterm=blended%20finance&keyword_select=exactphrase&strdate=1990-01-01&lang_exact=English&disclstat_exact=Disclosed&fl=txturl"]
object_ids_seen = []

with open("test_worldbank.json", "wt") as json_per_line_out:
    for query in queries:
        response = requests.get(query)
        objs = response.json()
        num_documents = objs["total"]
        num_pages = math.ceil(float(num_documents) / MAX_DOCS_PER_PAGE)
        
        for i in range(0, num_pages):
            x = 0 
            full_query = query + "&rows=" + str(MAX_DOCS_PER_PAGE) + "&os=" + str(i*MAX_DOCS_PER_PAGE)
            response = requests.get(full_query)
            objs = response.json()
            if len(objs["documents"]) > 0:
                for docname, document in objs["documents"].items():
                    if docname != "facets":
                        if document["id"] not in object_ids_seen and document["txturl"]:
                            print("did a thing!")
                            print(x)
                            x = x + 1 
                            response = requests.get(document["txturl"])
                            document["full_content"] = response.text
                            print("kept this document")
                            print(y) 
                            y = y + 1
                            if not re.search ("climat.*financ.*|mobilizing*private\sfinanc*|blended\sfinanc*", document["full_content"]):
                                break
                            object_ids_seen.append(document["id"])
                            json_per_line_out.write(json.dumps(document) + "\n")
                             