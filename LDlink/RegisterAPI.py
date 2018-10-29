#!/usr/bin/env python

# import sqlite3
import json


def register_user(firstnameInput, lastnameInput, emailInput, institutionInput, referenceInput):
    print firstname
    print lastname
    print email
    print institution
    print reference
    
    out_json = {
        firstname: firstnameInput,
        lastname: lastnameInput,
        email: emailInput,
        institution: institutionInput,
        reference: referenceInput
    }

    tmp_dir = "./tmp/"

    with open(tmp_dir + 'register_' + reference + '.json', 'w') as fp:
        json.dump(out_json, fp)

    return out_json
