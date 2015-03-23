__author__ = 'richss'

"""
The MIT License (MIT)

Copyright (c) 2015 Richard S. Stansbury

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

"""
    @author: Richard S. Stansbury
    Project:  QueryBot.py

    This is an initial twitter bot that does not post onto twitter, but rather runs a desired query
    on the streaming API.  It then performs a word count (eliminating some stop words).  Its final output
    is a list keywords and their counts.  The tweets are encoded from unicode to ascii, which eliminates most
    international tweets.  This is not perfect, but good enough for a first version.


    Requires a file named "twitterkeys.py" of the format:
        consumer_key = 'consumer_key'
        consumer_secret = 'consumer_secret'
        access_token = 'access_token'
        access_secret = 'access_secret'

    Requires stop-words (pip install stop-words)
    Requires tweepy (pip install tweepy)

    Reference: https://github.com/tweepy/examples/blob/master/streamwatcher.py
"""

import tweepy
import twitterkeys
import string
from stop_words import get_stop_words
import time

class StreamListener(tweepy.StreamListener):
    """
    Implements the Tweepy Stream Listener overriding on_status method.
    """

    keywords = {}
    banned = [v.encode('ascii') for v in get_stop_words('en')]
    time_limit = 0
    start_time = 0

    def __init__(self, limit, api=None):
        """
        Constructor for StreamListener class

        :param limit: time limit before this times out
        :param api: API (required by superclass)
        :return: N/A
        """
        super(StreamListener, self).__init__(api)
        self.time_limit = limit
        self.start_time = time.time()

    def on_status(self, status):
        """
        Handles Twitter Status Update (tweet) events.

        :param status: tweet to process
        :return: true if listener should continue, false if it should terminate (time limit)
        """

        # check if time limit (in seconds) is reached, if so, stop.
        if (time.time() - self.start_time) > self.time_limit:
            return False # terminate

        # print (time.time() - self.start_time), status.author.screen_name, '\t', status.text

        text = status.text.encode('ascii', 'ignore')  # convert to ascii from unicode
        text = text.translate(string.maketrans("", ""), string.punctuation) # remove punctuation
        words = text.split(" ") # split on spaces into a list.

        # remove short or stop words
        words = [string.lower(w).strip() for w in words if w not in self.banned and len(w) > 1]

        # add to the keywords list (method updates count per keyword)
        self.add_keywords(words)

        return True # continue running


    def get_keywords(self):
        """
        Returns the list of keywords in sorted order
        :return: sorted list of key words  (count, key)
        """
        return sorted([(v, k) for (k, v) in self.keywords.items()], reverse=True)

    def on_error(self, status_code):
        """
        Handles error event by printing out the error code and terminates
        listener

        :param status_code: error code
        :return: False, to force termination.
        """
        print "Error: " + str(status_code)
        return False

    def add_keywords(self, words):
        """
        Given a list of words, for each word, if already in the
        keyword dictionary, update the count (count+1); else, if new,
        add to the dictionary with count=1

        :param words: words to add
        :return: N/A
        """
        for w in words:
            if w not in self.keywords:
                self.keywords[w] = 1
            else:
                self.keywords[w] += 1

def main():
    """
    Handles the main task for the bot.
    :return: N/A
    """

    # Set up OAuth configuration given twitter API key (loaded from twiterkeys.py file)
    auth = tweepy.auth.OAuthHandler(twitterkeys.consumer_key, twitterkeys.consumer_secret)
    auth.set_access_token(twitterkeys.access_token, twitterkeys.access_secret)

    # Prompt user for query string
    query = raw_input('Enter Query (comma separated): ').split(',')

    # Create listener after prompting user for a time limit.
    listener = StreamListener(string.atoi(raw_input('Time Limit (seconds): ')))

    # Set up Stream and start filter given query
    twitterStream = tweepy.Stream(auth, listener, timeout=None)
    twitterStream.filter(track=query)

    # Once the filter terminates, receive the results from the listener class
    results = listener.get_keywords()

    # print the values (key, count) comma separated
    for (count, key) in results:
        print key + ", " + str(count)


if __name__ == '__main__':
    main()