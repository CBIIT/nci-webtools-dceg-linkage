#!/usr/bin/env python

# import sqlite3
import json


def register_user(firstname, lastname, email, institution, reference):
    print firstname
    print lastname
    print email
    print institution
    print reference
    
    out_json = {
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
        "institution": institution,
        "reference": reference
    }

    tmp_dir = "./tmp/"

    with open(tmp_dir + 'register_' + reference + '.json', 'w') as fp:
        json.dump(out_json, fp)

    return out_json
