from pymongo import MongoClient

def test_mongo(filename):

    try:
        contents=open(filename).read().split('\n')
        username=contents[0].split('=')[1]
        password=contents[1].split('=')[1]
        port=int(contents[2].split('=')[1])
        client = MongoClient('localhost', port)

    except ValueError, e:
            return "Error reading" + filename, e

    except client.errors.ConnectionFailure:
            print "MongoDB is down on port", port
            print "syntax: mongod --dbpath /local/content/ldlink/mongo/data/db/ --auth"
            return "Failed to connect to server. Please verify the contents of " + filename


    return "connected to server"

print(test_mongo("SNP_Query_loginInfo.ini"))