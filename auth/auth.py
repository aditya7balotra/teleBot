import json

with open('auth.json') as file:
    authData = json.load(file)
    
def auth(id):
    '''
    this function will return true if the given id matches any of the id from the auth.json file
    '''
    
    if id in authData['userid']:
        return True
    
    elif id in authData['groupid']:
        return True
    
    elif id in authData['channelid']:
        return True

    return False