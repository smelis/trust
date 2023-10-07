import os
import json
from post_comment_indicator import PostAnalysis
from dotenv import load_dotenv


def load_analysis_from_file(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return [PostAnalysis(**post_data) for post_data in data]


def process_comments_recursive(comment_analysis) -> int:
    total_comments = 1
    for reply in comment_analysis.comments:
        total_comments += process_comments_recursive(reply)
    return total_comments


def count_posts_and_comments(posts_analysis):
    posts = len(posts_analysis)
    comments = 0
    for post_analysis in posts_analysis:
        for comment_analysis in post_analysis.comments:
            comments += process_comments_recursive(comment_analysis)
    return posts, comments


def count(path):
    files = sorted([os.path.join(path, f) for f in os.listdir(path) if f.endswith('.json')], key=os.path.getctime)
    posts_total, comments_total = 0, 0
    for filename in files:
        posts_analysis = load_analysis_from_file(filename)
        posts, comments = count_posts_and_comments(posts_analysis)
        posts_total += posts
        comments_total += comments
    print(posts_total)
    print(comments_total)


load_dotenv('.env')
count(path=os.getenv("JSON_OUTPUT_DIR"))
