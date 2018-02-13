from requests.packages.urllib3.exceptions import ProtocolError
from collections import OrderedDict
from operator import itemgetter
from flask import Flask, Response, render_template
from textblob import TextBlob
import tweepy
import re
import string 
import datetime
import json

#python files
import private
import filter_users
import settings

app = Flask(__name__)


auth = tweepy.OAuthHandler(private.CONSUMER_KEY, private.CONSUMER_SECRET)
auth.set_access_token(private.ACCESS_TOKEN, private.ACCESS_TOKEN_SECRET)

api = tweepy.API(auth)

class StreamListener(tweepy.StreamListener):
    def __init__(self, start_time):
        """
        Initalizes a StreamListener object.
        start_time: the time the stream was connected
        tweets: a dictionary to store processed tweets and their polarity
        """
        tweepy.StreamListener.__init__(self)
        self.start_time = start_time
        self.tweets = {}
    
    def on_status(self, status):
        """
        Function called when the stream gets connected. Filters the tweets by user and language.
        If 30 seconds have passed since the stream was connected, returns False so stream can disconnect.
        """
        if filter_users.add_user(status) and status.lang == "en":
            self.process_tweet(status)
           
        #we want to collect tweets every 30 seconds so we set an internal timer inside the class
        if datetime.datetime.now() <= self.start_time + datetime.timedelta(seconds=30):
            return True
        
        return False
           
    def process_tweet(self, status):
        """
        Links, mentions, "RT"s, emojis, and stopwords are removed from the tweet. Sentiment anlaysis is performed and 
        the clean tweet (sans stopwords) and analysis result is stored in the tweets dict.
    
        status: a status object
        
        """
        #remove links, mentions, "RT"s, emojis, non-ascii chars from the tweet
        clean_tweet = re.sub(r"([^\w]?:\@|https?\://)\S+", "", status.text)
        clean_tweet = re.sub(r'[^\x00-\x7F]+'," ", clean_tweet)
        
        clean_tweet = clean_tweet.replace("RT ", "")
        
        #remove numbers and punctuation
        translator = str.maketrans("", "", string.punctuation + string.digits)
        clean_tweet = clean_tweet.translate(translator)

        
        clean_tweet = clean_tweet.lower()
        
        #https://stackoverflow.com/questions/2400504/easiest-way-to-replace-a-string-using-a-dictionary-of-replacements/2400577#2400577
        slang = re.compile(r'\b(' + '|'.join(settings.SLANG_DICT.keys()) + r')\b')
        clean_tweet = slang.sub(lambda x: settings.SLANG_DICT[x.group()], clean_tweet)
        ####

        polarity = StreamListener.get_polarity(clean_tweet)
        
        #remove stopwords(using the custom stopwords list in settings.py) to get most important words
        important_words = " ".join([word for word in clean_tweet.split() if word not in settings.STOPWORDS_SET])
        
        #add the processed tweet into the tweets list
        self.tweets[important_words] = polarity
    
    @staticmethod      
    def get_polarity(tweet):
        """
        Determines the polarity of the tweet using TextBlob.
        
        tweet: a partially processed tweet (still has stopwords)
        return: int polarity -> 1 if positive, 0 if neutral, -1 if negative
        
        """
        
        text_blob = TextBlob(tweet)
        
        tweet_polarity_float = text_blob.sentiment.polarity
        
        #greater than 0.05 ->  positive, less than -0.05 -> negative, else neutral
        if tweet_polarity_float >= 0.05:
            polarity = 1
        elif tweet_polarity_float <= -0.05:
            polarity = -1
        else:
            polarity = 0
        
        return polarity

        
    def get_tweets(self):
        """
        Returns a copy of the tweets dictionary.
        """
        return self.tweets.copy()
    
    def on_error(self, status_code):
        """
        Handles errors coming from the Twitter API. If being rate limited, 
        Twitter will send a 420 status code and we will disconnect.
        
        """
        if status_code == 420:
            return False


class SortData(object):
    data = {}
    
    def __init__(self, tweets):
        """
        Initializes a SortData object.
        tweets: a dictionary of processed tweets and their polarity
        """
        self.tweets = tweets
        
    def calculate_frequencies(self):
        """
        Calculates the frequencies of the words in processed tweets
        and creates the data dictionary. A key value pair for the dictionary 
        will have the word as the key and a list as its value. The list will include
        the number of times the word has occurred in all the tweets seen so far and 
        another list including the number of positive, neutral, and negative tweets
        containing that word.
        
        """
        #key value pair for the data dictionary -> word:[count, [numPositiveTweets, numNeutralTweets, numNegativeTweets]]
        
        for tweet, polarity in self.tweets.items():
            for word in tweet.split():
                if word not in self.data:
                    
                    self.data[word] = [0, [0, 0, 0]]
                    
                    self.data[word][0] = 1
                    
                    self.update_polarity_frequency(word, polarity)
                
                else:
                    self.data[word][0] += 1
                    
                    self.update_polarity_frequency(word, polarity)
                    
                        
    def update_polarity_frequency(self, word, polarity):
        """
        Determines what polarity (positive, neutral, negative) the tweet has 
        according to the tweets dictionary and updates the value in the data dictionary.
        
        """
        if polarity == 1:
            self.data[word][1][0] += 1
        elif polarity == 0:
            self.data[word][1][1] += 1
        else:
            self.data[word][1][2] += 1
        
                    
    def get_most_common_words(self):
        """
        Removes all the words in the data dictionary that have occurred
        less than two times in all the tweets seen so far. Sorts the data
        dictionary by frequency of the words in descending order.
        
        return: a JSON object version of the sorted dictionary 
        
        """
        self.calculate_frequencies()
        
        data_copy = self.data.copy()
        
        for word in data_copy:
             if self.data[word][0] <= 2:
                 del self.data[word]
                 
        sorted_words = OrderedDict(sorted(self.data.items(), key = itemgetter(1), reverse = True))
        
        #make sure the dictionary is less than or equal to 15 words so ajax request in javascript 
        #doesn't slow down
        while len(sorted_words) >= 15:
            sorted_words.popitem()
        return json.dumps(sorted_words)

def event_stream():
    """
    Connects the stream, sorts and processes the data, and creates
    a dictionary of the most common words found.
    
    return: a JSON object containing the most common words found in the tweets sample 
            and their frequencies and polarity data
    
    """
    try: 
        stream_listener = StreamListener(datetime.datetime.now())
        stream = tweepy.Stream(auth = api.auth, listener = stream_listener)
        #we want a lot of tweets so we filter with most used words
        stream.filter(track = settings.COMMON_WORDS, locations = settings.LOCATIONS)
        stream.disconnect()
        sortData = SortData(stream_listener.get_tweets())
        return sortData.get_most_common_words()
    except ProtocolError:
        print("There was an error. Restarting stream...")
    except ConnectionError:
        print("There was an error. Restarting stream...") 




@app.route('/')
def index():
    #clear the data dictionary when page is refreshed
    SortData.data.clear()
    return render_template("index.html")

@app.route('/stream')
def stream(): 
    return Response(event_stream(), mimetype="application/json")

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html")

@app.errorhandler(500)
def internal_server_error(error):
    return render_template("500.html")
              

if __name__ == '__main__':     
    app.debug = True
    app.run(threaded=True)