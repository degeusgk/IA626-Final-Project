#Final Project - IA626
# By Grace De Geus
#---------------------------------------------

import praw,json,csv,datetime,time
start = time.time()
#Access Reddit
reddit = praw.Reddit(client_id = 'hANTyPawYnpakQ', client_secret = 'mPssnqE6D4U_Jd04oxrEZ8UDAfk', username = 'Ia626_Final', password = 'Ia626_Final', user_agent = 'IA626')

Output_File = open("results.txt",mode="w", encoding="utf8")

#File manipulation, make sure we start with an empty output file
excel_file = open('Comment_Data.csv','w')
excel_writer = csv.writer(excel_file, delimiter=',',lineterminator='\n')
output = ["Subreddit", "Post ID", "Post Title", "Comments per Post", "Date/time of Post", "Removed Comments per Post", "% of Comments Removed", "Comments We Counted"]
excel_writer.writerow(output)

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

post_number = 1
conversedict = {}
removal_reason_hist = {}
removed_number = 0


subreddits = [reddit.subreddit('coronavirus').top('month', limit=25), reddit.subreddit('COVID19').top('month', limit=25)]


#Iterate through all sebreddits in my list
for subreddit in subreddits:
    #Iterate through all posts in this subreddit
    for submission in subreddit:
        Output_File.write("\n")
        Output_File.write(submission.title)
        Output_File.write("\nComment Total: ")
        Output_File.write(str(submission.num_comments))
        Output_File.write("\n")
        #Load all comments
        submission.comments.replace_more(limit=None)
        #Reset count of removed comments for this new post
        removed_count = 0
        #Iterate through all comments on this post
        comment_number = 0
        for comment in submission.comments.list():
            #If we have not read this comment before
            if comment.id not in conversedict:
                #Add it to our dictionary for later
                conversedict[comment.id] = [comment.body]
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
                    
                #If there are replies to this comment, we need to traverse them as well
                if len(comment.replies) > 1:
                    traverse_replies(comment.replies)
                    

            comment_number += 1
        #Normalize percentage and date/time data
        removed_count_percent = round((removed_count/submission.num_comments)*100,2)
        post_datetime = datetime.datetime.fromtimestamp(int(submission.created_utc)).strftime('%Y-%m-%d %H:%M:%S')
        
        #           Subreddit,            Post ID,       Post Title,       Comments per Post,       Date/time of Post,Removed Comments per Post, % of Comments Removed, Comments We Counted
        next_row = [submission.subreddit, submission.id, submission.title, submission.num_comments, post_datetime, removed_count, removed_count_percent, comment_number]
        excel_writer.writerow(next_row)

        post_number += 1
        print("Still good...\n")

#Calculate the total number of comments removed by moderators
total_removed = 0
for reason in removal_reason_hist:
    total_removed += removal_reason_hist[reason]


Output_File.write(json.dumps(removal_reason_hist))
Output_File.write("\nTotal comments removed: {} \n".format(str(total_removed)))
Output_File.write(str(time.time() - start)) 
#Close files
excel_file.close()   
Output_File.close()