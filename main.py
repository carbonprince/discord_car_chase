import requests
import json
from discord import Webhook, RequestsWebhookAdapter, Embed
import traceback
import time

# NOTE: To activate your python environment use the command
# .\my_env\Scripts\activate

def get_config(path):
    """
    Takes the contents of a .json file that exists locally and 
    returns the contents as a dictionary
    """
    config_file = open(path, 'r') # see https://www.w3schools.com/python/ref_func_open.asp
    return json.loads(config_file.read()) # see https://www.geeksforgeeks.org/json-loads-in-python/#:~:text=loads()%20method%20can%20be,JSON%20data%20into%20Python%20Dictionary.

config = get_config('config.json') # we put this outside of the functions so it can be accessed globally 

def create_url(user_id):
    """
    Takes a twitter user id and puts it into a 
    url and returns the url
    """
    return f"https://api.twitter.com/2/users/{user_id}/tweets"

def get_params():
    """
    Returns a dictionary of keys with single values to request to the api
    tweet.fields values can be seen at https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/tweet
    """
    # Tweet fields are adjustable.
    # Options include:
    # attachments, author_id, context_annotations,
    # conversation_id, created_at, entities, geo, id,
    # in_reply_to_user_id, lang, non_public_metrics, organic_metrics,
    # possibly_sensitive, promoted_metrics, public_metrics, referenced_tweets,
    # source, text, and withheld
    return {"tweet.fields": "created_at", "tweet.fields": "entities"}

def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    Takes a request and sets the request headers "Authorization" and "User-Agent" with values that we define 
    See: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Authorization
    """
    r.headers["Authorization"] = f"Bearer {config['bearer_token']}"
    r.headers["User-Agent"] = "v2UserTweetsPython"
    return r


def connect_to_endpoint(url, params):
    """
    Send a GET request to our api endpoint at the custom url
    authorize our reqeust using the output of the bearer_oauth() function 
    Send the value of the 'params' variable with the request

    Return the .json output of the response of the "GET" request 

    For more info in requests.rquest see:
    https://www.codecademy.com/resources/docs/python/requests-methods/request
    """
    response = requests.request("GET", url, auth=bearer_oauth, params=params)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            f"Request returned an error: {response.status_code} {response.text}"
            )
    return response.json()

def filter_json(tweet, past_id):
    if "WATCH LIVE" in tweet['text']:
        if int(tweet['id']) > past_id:
            return tweet['entities']['urls'][0]['expanded_url'] 

def set_latest_tweet_id(json_response):
    newest_id = json_response['meta']['newest_id']
    with open("past_ids.txt", mode="w+") as file:
        file.write(f"{newest_id}")

def get_latest_tweet_id():
    try:
        with open("past_ids.txt", mode="r") as file:
            latest_tweet_id = file.read()
            return int(latest_tweet_id)
    except FileNotFoundError:
        return 0

def main():
    webhook_url = config['webhook_url']
    url = create_url(config['twitter_account']) # get a url to the twitter api with the account_id inserted into it
    params = get_params() # get the parameters to send to the API via a request 
    while True:
        json_response = connect_to_endpoint(url, params) # make a request to the api endpoint at the <url> using the <params>   
        latest_tweet_id = get_latest_tweet_id()
        if int(json_response['meta']['newest_id']) > latest_tweet_id:
            tweet_urls = []
            for tweet in json_response['data']:
                tweet_urls.append(filter_json(tweet))
            for url in tweet_urls:
                webhook = Webhook.from_url(webhook_url, adapter=RequestsWebhookAdapter()) # Initializing webhook
                webhook.send(content=f"🚨CHASE ALERT🚨\n{url}")
                ## NOTE: below is commented out for now until we can get rich preview on            
                # embed = discord.Embed(title="CHASE", description="🚨") # Initializing an Embed
                # embed.add_field(name="Link", value= url) # Adding a new field
                # webhook.send(embed=embed) # Executing webhook and sending embed.
            set_latest_tweet_id(json_response)
        time.sleep(60)

if __name__ == "__main__":
    main()

# Example outputs of tweets 
# Each tweet is separated by three newlines 
