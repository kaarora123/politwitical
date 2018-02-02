#other users whose status properties do not match the ones below
USERS = ["realDonaldTrump", "AP", "TheDemocrats", "dscc", "dccc", "GOP", "POTUS", 
         "SenateGOP", "HouseGOP", "KellyannaPolls", "politico", "NBCPolitics", "thehill", 
         "FLOTUS", "WhiteHouse", "mike_pence", "IvankaTrump", "SpeakerRyan", "Liz_Wheeler", 
         "FoxNews", "cnnbrk", "dbongino", "BuzzFeedNews", "ACLU", "TwitterGov", "MoveOn", "chuckschumer"
         "nytimes", "NYCMayor", "JRosenwrocel", "MClyburnFCC", "PreetBharara", "BarackObama", 
         "MichelleObama", "NBCNews", "Reuters", "GenFlynn", "kylegriffin1", "JoyAnnReid", "AnnCoulter",
         "Comey", "JeffreyToobin", "waltshaub", "NBCNews", "MSNBC", "People4Bernie", "ggreenwald", 
         "latimes", "TPM", "HuffPostPol", "ABCPolitics", "CNNPolitics", "foxnewspolitics", "NBCPolitics",
         "CBSPolitics", "bpolitics", "donnabrazile"]

USERS_SET = set(USERS)

MIN_FOLLOWER_COUNT = 1000

buzzwords = ["clinton", "obama", "trump", "sanders", "resist", "persist", "maga", "advocate", "democrat", 
             "republican", "dem", "liberal", "conservative", "dnc", "gop", "politic", "military", "democracy"
             "wall", "activist", "delegate", "assembly", "city council", "attorney", "russia", "cnn", "fox", 
             "activism"]


def add_user(status):
    """
    Determines whether or not to add a user's tweet to the sample based on whether or not  
    they are a politician, they are an influential political twitter account, or they are in the USERS list. 
    status: a status object
    return: boolean True if the tweet should be added, False otherwise
    
    """
    if is_senator(status) or is_rep(status) or is_in_congress(status) or is_mayor(status) or is_governor(status):
        return True
    if status.user.screen_name in USERS_SET:
        return True
    if has_buzzwords(status) and is_influential(status):
        return True
    return False
        

def is_in_congress(status):
    """
    Determines whether or not a user is in congress based on their description.
    status: a status object
    return: boolean
    """
    if status.user.description != None:
        if "congress" in status.user.description.lower():
            return True
    return False
    
def is_rep(status):
    """
    Determines whether or not a user is a representative based on their name, screen name, 
    or description.
    return: boolean
    """
    if "Rep" in status.user.screen_name or "Rep" in status.user.name:
        return True
    if status.user.description != None:
        if "Representative" in status.user.description:
            return True
    return False

def is_governor(status):
    """
    Determines whether or not a user is a governer based on their name, screen name,
    or description.
    return: boolean
    """
    if "Gov" in status.user.screen_name or "Gov" in status.user.name:
        return True
    if status.user.description != None:
        if "Governor" in status.user.description:
            return True
    return False

def is_mayor(status):
    """
    Determines whether or not a user is a mayor based on their name, screen name,
    or description.
    return: boolean
    """
    if "Mayor" in status.user.screen_name or "Mayor" in status.user.name:
        return True
    if status.user.description != None:
        if "Mayor" in status.user.description:
            return True
    return False

def is_senator(status):
    """
    Determines whether or not a user is a senator based on their name, screen name,
    or description.
    return: boolean
    """
    if "Sen" in status.user.screen_name or "Sen " in status.user.name:
        return True
    
    if status.user.description != None:
        if "Sen." in status.user.description or "Senator " in status.user.description:
            return True
    return False
      

def has_buzzwords(status):
    """
    Determines whether or not the user has any of the political buzzwords specified in the buzzwords list
    in their description.
    status: a status object
    return: boolean True, if the description contains buzzwords, False otherwise
    """
    for word in buzzwords:
        if status.user.description != None:
            if word in status.user.description.lower():
                return True
    return False


def is_influential(status):
    """
    Determines whether or not a user is influential based on their follower count.
    status: status object
    return: boolean 
    """
    if status.user.followers_count >= MIN_FOLLOWER_COUNT:
        return True
    return False