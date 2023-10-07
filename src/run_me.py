import praw
import openai
from datetime import datetime

from post_comment_indicator import PostAnalysis, CommentAnalysis

openai_api_key = "env"
openai.api_key = openai_api_key


def categorize_text(text):
    all_categories = [
        "Expression of Empathy and Support",
        "Positive Endorsement or Advocacy",
        "Skepticism or Questioning",
        "Criticizing or Blaming",
        "Reliance on Objective Evidence or Credible Sources",
        "Ignoring or Neglecting a Perspective",
        "Indirect Implications or Innuendo",
        "Historical Trust or Distrust",
        "Conditional Trust or Distrust",
        "Recognition of Reformed or Changed Trust"
    ]

    category_prompt = "\n".join(all_categories)

    prompt_text = f"""
Your next task is to categorize the following text in terms of the categories of trust and distrust provided at the 
bottom.
 
IF a category of trust or distrust is applicable ALWAYS return the FULL NAME of the category. 
DO NOT SHORTEN OR ABBREVIATE IT. 
DO NOT ADD EXTRA INFORMATION. 
JUST PRINT THE CATEGORY NAME OR NAMES IF THEY APPLY OTHERWISE *NOTHING* AND NOTHING FURTHER.

Example:
```Text:
Johnny is a famous movie star and I love him, therefore he's right.
```

````Result:
Ignoring or Neglecting a Perspective
Conditional Trust or Distruct
Historical Trust or Distrust
Positive Endorsement or Advocacy
```

Example of a wrong result:
```
Ignoring or Neglecting a Perspective
note this text does not contain any indicators of trust or distrust.
```

The text:
{text}

The categories of trust and distrust by which to categorize:
{category_prompt}
"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=[{"role": "system", "content": "You are an amazing literary scholar skilled in recognizing "
                                                "indicators of trust and distrust in texts. You're to the point"
                                                "and practical. You perform monotonous tasks like you will get"
                                                "correctly, diligently and without being chatty. You are a"
                                                "focussed machine!"},
                  {"role": "user", "content": prompt_text}]
    )

    applicable_categories = {}
    print(response.choices[0].message['content'].lower())
    for category in all_categories:
        if category.lower() in response.choices[0].message['content'].lower():
            applicable_categories[category] = True
        else:
            applicable_categories[category] = False

    return applicable_categories


def fetch_and_categorize_subreddit(subreddit_name: str):
    # Configure Reddit API client
    reddit = praw.Reddit(
        client_id="env",
        client_secret="env",
        user_agent="test-trust",
    )

    sub = reddit.subreddit("JusticeForJohnnyDepp")
    submissions = sub.new(limit=1)
    posts_analysis = []
    for submission in submissions:
        post_creation_time = submission.created_utc
        print(datetime.utcfromtimestamp(post_creation_time))
        author = reddit.redditor(name=submission.author)
        post_analysis = PostAnalysis(
            post_title=submission.title,
            post_text=submission.selftext,
            categories=categorize_text(submission.title + "\n\n" + submission.selftext),
            date_time=datetime.utcfromtimestamp(post_creation_time),
            author=submission.author.name,
            author_karma=author.link_karma,
            author_flair=submission.author_flair_text,
            comments=[]
        )

        submission.comments.replace_more(limit=None)  # Fetch all comments
        for comment in submission.comments.list():
            comment_creation_time = comment.created_utc
            comment_analysis = CommentAnalysis(
                comment_text=comment.body,
                categories=categorize_text(comment.body),
                date_time=datetime.utcfromtimestamp(comment_creation_time),
                author=comment.author.name if comment.author else "Deleted",
                author_karma=comment.author.link_karma if comment.author else 0,
                author_flair=comment.author_flair_text if comment.author else None
            )
            post_analysis.comments.append(comment_analysis)
        posts_analysis.append(post_analysis)

    return posts_analysis


analysis = fetch_and_categorize_subreddit(
    subreddit_name="JusticeForJohnnyDepp"
)

print(analysis)

