import time
import os
import praw
import json
from datetime import datetime
from pydantic import ValidationError
from post_comment_indicator import PostAnalysis, CommentAnalysis
from dotenv import load_dotenv


def get_author_karma(author):
    try:
        if author:
            result = author.link_karma if author and author.link_karma else 0
        else:
            result = 0
    except AttributeError:
        result = 0
    return result


def fetch_comments(comment_list, indent=2):
    """
    Recursively fetches comments and their replies.
    """
    comments_analysis = []
    for comment in comment_list:
        print('  ' * indent + f"On {datetime.utcfromtimestamp(comment.created_utc).isoformat()} "
                              f"{comment.author} posted a new comment. Analyzing...")

        # indicators = find_trust_indicators(comment.body)
        comment_analysis = CommentAnalysis(
            comment_text=comment.body,
            fullname=comment.fullname,
            trust_indicators=[],
            date_time=datetime.utcfromtimestamp(comment.created_utc).isoformat(),
            author=comment.author.name if comment.author else "Deleted",
            author_karma=get_author_karma(comment.author),
            author_flair=comment.author_flair_text if comment.author else None,
            comments=fetch_comments(comment.replies, indent=indent + 2) if comment.replies else [],
            url="https://www.reddit.com" + comment.permalink
        )
        comments_analysis.append(comment_analysis)

    return comments_analysis


def get_last_saved_post_fullname(path):
    files = sorted([os.path.join(path, f) for f in os.listdir(path)], key=os.path.getctime, reverse=True)
    if files:
        with open(files[0], 'r') as file:
            data = json.load(file)
            if data:
                last_post = data[-1]  # Last post in the last saved file
                return last_post['fullname']
    return None


def save_analysis_to_file(posts_analysis, filename):
    with open(filename, 'w') as file:
        json.dump([p.model_dump() for p in posts_analysis], file, indent=4)
    print(f"Analysis saved to {filename}")


def fetch_and_categorize_subreddit(subreddit_name: str, path, after_id=None):
    # Configure Reddit API client
    reddit = praw.Reddit(
        client_id="env",
        client_secret="env",
        user_agent="test-trust",
    )

    sub = reddit.subreddit(subreddit_name)
    if after_id:
        submissions = sub.new(limit=None, params={"after": after_id})
    else:
        submissions = sub.new(limit=None)
    posts_analysis = []
    first_post_time = None

    for submission in submissions:
        if not first_post_time:
            first_post_time = datetime.utcfromtimestamp(submission.created_utc).isoformat()

        print(f"On {datetime.utcfromtimestamp(submission.created_utc)} {submission.author} posted a new submission "
              f"with title {submission.title}. Analyzing...")
        try:
            post_analysis = PostAnalysis(
                post_title=submission.title,
                post_text=submission.selftext,
                fullname=submission.fullname,
                trust_indicators=[],
                date_time=datetime.utcfromtimestamp(submission.created_utc).isoformat(),
                author=submission.author.name if submission.author else "Deleted",
                author_karma=get_author_karma(submission.author),
                author_flair=submission.author_flair_text,
                comments=[],
                url="https://www.reddit.com" + submission.permalink
            )
        except ValidationError as e:
            print(e)
            print([])

        submission.comments.replace_more(limit=None)  # Fetch all comments
        post_analysis.comments = fetch_comments(submission.comments)
        posts_analysis.append(post_analysis)
        time.sleep(5)

        print(f"Number of posts in this batch: {len(posts_analysis)}")

        if len(posts_analysis) >= 1:
            last_post_time = datetime.utcfromtimestamp(submission.created_utc).isoformat()
            safe_start_time = first_post_time.replace(":", "-").replace("T", "_").replace("Z", "")
            safe_end_time = last_post_time.replace(":", "-").replace("T", "_").replace("Z", "")
            filename = f'{path}/{subreddit_name}_{safe_start_time}_{safe_end_time}.json'
            save_analysis_to_file(posts_analysis, filename)
            posts_analysis = []
            first_post_time = None

    if posts_analysis:
        last_post_time = datetime.utcfromtimestamp(submission.created_utc).isoformat()
        safe_start_time = first_post_time.replace(":", "-").replace("T", "_").replace("Z", "")
        safe_end_time = last_post_time.replace(":", "-").replace("T", "_").replace("Z", "")
        filename = f'{path}/{subreddit_name}_{safe_start_time}_{safe_end_time}.json'
        save_analysis_to_file(posts_analysis, filename)

    return posts_analysis


trust_path = 'D:\\data\\tilburguniversity\\inge\\trust'
last_saved_fullname = get_last_saved_post_fullname(trust_path)

analysis = fetch_and_categorize_subreddit(
    subreddit_name="JusticeForJohnnyDepp",
    path=trust_path,
    after_id=last_saved_fullname
)
