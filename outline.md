# IA626 Final Project
###### By: Grace De Geus
### Data Sources:
-Reddit
### API and Code used
https://www.reddit.com/dev/api/

https://praw.readthedocs.io/en/latest/

https://pythonprogramming.net/introduction-python-reddit-api-wrapper-praw-tutorial/

https://pythonprogramming.net/parsing-comments-python-reddit-api-wrapper-praw-tutorial/?completed=/introduction-python-reddit-api-wrapper-praw-tutorial/

## Project Summary
General starting point: How much misinformation on the COVID-19 pandemic is being shared on social media?

Due to the current global pandemic of COVID-19 there has been an obvious spike in information regarding viruses, including their mortality rate, infection mechanisms, number and rate of new cases, and how local, state, national, and global communities and governments have reacted to the pandemic. I am interested in trying to determine how much misinformation is being spread on social media. I have heard the spread of misinformation described as an "infodemic". The misinformation being shared most likely plays a role in the spread of the disease itself. I am looking to pull data from Reddit, which has very well moderated caronavirus subreddits. I'd like to compare comment data pulled from coronavirus related subreddits to see how they compare in terms of number of comments removed by moderators for violations of the subreddit rules. I would also like to determine the reasons for removing these comments.
### Overview
![png](https://github.com/degeusgk/IA626-Final-Project/blob/master/Overview_Flowchart.png)
### Approach
My approach for this started with an investigation into how to retrieve comment information from Reddit. Thankfully Reddit has a readilly available API; just sign up with an account, register with the site the desire to create a script, app, or bot, and receive API credentials.

Now, working with an API might be pretty straightforward, but the Reddit community (where it intersects with the programming community) has developed a wrapper for this API to make it even easier. The Python Reddit API Wrapper (PRAW) aims to be as easy to use as possible, but the main advantage is that the wrapper is designed to follow all of reddit's API rules. These rules are a little extensive and, without keeping each in mind when programming, it wouldn't be very hard to break them. The added peace of mind that comes from the wrapper is greatly appreciated. As such, I only briefly consulted the Reddit API and referenced the PRAW website almost exclusively.

In order to utilize PRAW, one has to import it:
```python
import praw,json,csv,datetime,time
```
I also imported json and csv in order to output data to text and csv files for later analysis. Datetime was imported to manipulate the date/time for each submission and comment retrieved from each subreddit. Time was imported to allow me to time how long the script takes to run (hint: it's a long time).

Next, the most important thing to do is create a Reddit instance. I followed the 'Introduction to Python Reddit API Wrapper PRAW Tutorial' (linked above). This requires a Client ID, Client Secret, Username, Password, and User Agent. The Username, Password, and User Agent are required to be given when requesting API access on the Reddit website, and the Client ID and Client Secret are provided when that access is granted (I have redacted the sensitive information in the code snippet below). 
```python
reddit = praw.Reddit(client_id = 'xxx', client_secret = 'xxx', username = 'Ia626_Final', password = 'xxx', user_agent = 'IA626')
```
In order to start pulling data from Reddit I first needed to decide where to pull data from. I settled on r\coronavirus and r\COVID-19. These two subreddits have a reputation for being very well moderated, meaning mods are active and quick to remove comments violating the rules, and also have strict rules for what types of information are allowed to be shared. 
```python
subreddits = [reddit.subreddit('coronavirus').top('month', limit=25), reddit.subreddit('COVID19').top('month', limit=25)]
```
The ```subreddit()``` function retuns an instance of subreddit requested by name. The ```top()``` function, when provided with a timeframe and post limit, returns a list of posts, or submissions, meeting that specification. The other options for this type of data mining are ```hot()``` or ```new()```.  I presumed that the top posts would give a more indicative sample.
I selected the top 25 posts from the past month from each subreddit. This covers the month of April and would have given each post time to collect a decent amount of comments. I pulled  posts with as few as 42 comments, to as many as 5707 comments. My estimation was that this was a wide enough range of time and popularity to be a statistically significant sample to analyze.

I used a nested loop to iterate through first the subreddits in my list, and then the posts (submissions) on each subreddit. 
```python
#Iterate through all sebreddits in my list
for subreddit in subreddits:
    #Iterate through all posts in this subreddit
    for submission in subreddit:
```
Each submission instance has an attribute ```comments```. This attribute is interesting as it returns a ```commentforest``` which contains all replies to this comment, and all associated data. A forest of comments starts with multiple top-level comments. Each of these comments can be a tree of replies. However, when the original call for comments is made, as is true when accessing the website normally, there is a limit to the number of comments displayed. Anything further than that is obscured with a "load more comments" button on the website, and a similar instance in the comment forest by way of MoreComment objects. PRAW has a ```replace_more()``` function wich will replace MoreComment objects for you, with a limit of 32. Each MoreComments object replacement requires another API call, which counts against your quota (30 API requests per minute).
```python
        #Load all comments
        submission.comments.replace_more(limit=None)
```
After retrieving all comments for a submission, I need to "flatten" out the comment forest in order to effectively traverse it. This is done by using the ```list()``` function on the comment. This returns a list of all replies made to the base comment. 
```python
        #Reset count of removed comments for this new post
        removed_count = 0
        #Iterate through all comments on this post
        comment_number = 0
        for comment in submission.comments.list():
```
I then check to see whether I have reviewed the comment yet by placing it in a dictionary using the comment's ID as the Key. I only want to count each removed comment once. I got this idea from the PythonProgramming.net Parsing comments python reddit API wrapper PRAW tutorial (linked above).
```python
            #If we have not read this comment before
            if comment.id not in conversedict:
                #Add it to our dictionary for later
                conversedict[comment.id] = [comment.body]
```
This is where the comments get interesting. After observing the comment content for removed comments, and their associated attributes, I identified the way to determine if a comment was removed by a moderator was to look at the replies. If a mod removes a comment they reply to that removed comment with a reason for it's removal. The reply states that it was indeed a mod who removed the comment, and the reason is listed with "\*\*" surrounding it. Therefore, if a comment contains the term "removed" and the "\*\*", it can be assumed that a mod removed a comment. I tested each unique comment for this combination and, if found, split that comment on the "\*\*".  I could then easilly select the removal reason from the comment text, and track it in a histogram using the text itself as the Key.
```python
                #If this comment is a "removed by moderator" response
                if "removed" in comment.body and "* **" in comment.body: 
                    #Add to removed_count for this post
                    removed_count += 1
                    #Capture the reason for comment removal
                    removal_reason = comment.body.split("**")[1]
                    #Add it to the histogram for later analysis
                    if removal_reason not in removal_reason_hist:
                        removal_reason_hist[removal_reason] = 1
                    else:
                        removal_reason_hist[removal_reason] += 1
```
The trick with comments is that most of them have replies, and I needed to check each of the replies for additional removed comments. I created a function to handle that activity. If there are replies, then traverse them.
```python
                #If there are replies to this comment, we need to traverse them as well
                if len(comment.replies) > 1:
                    traverse_replies(comment.replies)
```
This function takes in a ```commentforest``` as its sole argument, and cycle through the list searching for any reasons for removed comments. Then, if the reply I am scraping has replies of its own, I recursively call ```traverse_replies()``` until I reach the base condition of no more replies. In this way I effectively move through the entire ```commentforest``` and find all possible instances of comments removed by moderators.
```python
def traverse_replies(replies_list):
    #replies_list is a comment forest, reply is one comment object
    for reply in replies_list:
        body = reply.body
        if "removed" in body and "* **" in body:            
            removal_reason = body.split("**")[1]
            if removal_reason not in removal_reason_hist:
                removal_reason_hist[removal_reason] = 1
            else:
                removal_reason_hist[removal_reason] += 1  
            
        if len(reply.replies) > 1:   
            traverse_replies(reply.replies)
            
    return
```
Once all comments have been traversed, I captured the data for each post in a .csv file. This would allow me to easilly graph the data against eachother and over time. The datetime data needed to be normalized. This attribute is stored in UNIX time and must be translated into something human readable. I chose the following format. In addition I calculated the percentage of removed comments based on the number I counted verses the total comments reported for that post.
```python
        #Normalize percentage and date/time data
        removed_count_percent = round((removed_count/submission.num_comments)*100,2)
        post_datetime = datetime.datetime.fromtimestamp(int(submission.created_utc)).strftime('%Y-%m-%d %H:%M:%S')
```
Finally, I calculated the total number of comments removed by moderators by adding all totals captured in my comment removal reason histogram.
```python
#Calculate the total number of comments removed by moderators
total_removed = 0
for reason in removal_reason_hist:
    total_removed += removal_reason_hist[reason]
```
These data were then output to a .txt file using ```json.dumps()``` for a nicely formatted historgram for easy reading, without cluttering my .csv.

 ### Hypothesis: 
 There are more posts removed due to misinformation in the r\COVID-19 subreddit than the r\coronavirus subreddit.
 
 #### Analysis
 I graphed the number of removed comments for each of the subreddits over the time period in which they were posted. It quickly became obvious that r\COVID19 consistently has significantly fewer removed comments than r\coronavirus.
 
![png](https://github.com/degeusgk/IA626-Final-Project/blob/master/Removed_Comments_Over_Time.png)

When comparing the proportion of removed comments to the whole the difference is equally as stark. Not only does r\coronavirus have more removed comments, it has a higher percentage of comments that are removed. This is despite the fact that for every moderator removed comment there is an additional comment explaining why.


![png](https://github.com/degeusgk/IA626-Final-Project/blob/master/Percent_Removed_Comments_Over_Time.png)

 ### Conclusions:
The r\COVID19 has fewer bad actors, and therefore comments removed, than r\coronavirus. I was surprised by this finding. My assumption of the opposite was based on the fact that r\COVID19 is the "scientific sister" subreddit to r\coronavirus. I thought there would be more of an attempt to spread misinformation there. But now I see how it might be harder to provide bad scientific data than to spread more general misinformation, as one would on r\coronavirus. 
Overall I found this a very interesting conclusion.