import os
import re
import ast
import json
import time
from post_comment_indicator import PostAnalysis, CommentAnalysis, TrustIndicator
import openai
from openai.error import Timeout, APIError

openai.api_key = "env"


def get_chat_completion(system_prompt, prompt, temp=0.5, model="gpt-3.5-turbo"):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            temperature=temp,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": prompt}]
        )
    except (APIError, Timeout) as t1:
        time.sleep(5)
        try:
            response = openai.ChatCompletion.create(
                model=model,
                temperature=temp,
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": prompt}]
            )
        except (APIError, Timeout) as t2:
            time.sleep(60)
            response = openai.ChatCompletion.create(
                model=model,
                temperature=temp,
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": prompt}]
            )
    return response


def find_trust_indicators(text):
    system_prompt = r"""
You are a skilled PhD student in social media studies and will be given tasks involving texts which have to be analyzed. 
You are a practical worker and you follow instructions to the letter.
    """

    prompt_text = r"""
**IMPORTANT: If the provided text is insufficient, unclear, or missing, simply return an empty array `[]`.**
**IMPORTANT: Always return a complete array of JSON objects. Never end it with an ellipsis.**

You're analyzing a series of texts related to the trial between Johnny Depp (often referred to as "JD") and Amber 
Heard (often referred to as "AH"). The texts are submissions and comments taken from the subreddit 
r/JusticeForJohnnyDepp on Reddit. The texts might contain profanities, memes, URLs, inside jokes, or other 
distractions. If the text contains only spam or an image, or if no text is provided, simply return an empty array.

Your task is to identify indicators of trust or distrust towards Johnny Depp, Amber Heard, or entities related to 
them (e.g. family, lawyer, friend, colleague, etc.). Your response should be in the JSON format, and must be brief 
since it'll serve as input for a software application. Don't look for anything other than indications of trust or 
distrust.

Your response should be one array containing individual dictionaries for each indicator of (dis)trust.

For a single indicator:
```
[{ "category": "trust", "towards": "Amber Heard", "why": "Expression of empathy", "relation": "" }]
```

For multiple indicators, all elements should still be in a single array:
```
[ { "category": "trust", "towards": "Johnny Depp", "why": "Positive endorsement", "relation": "" }, { "category": "distrust", "towards": "Amber Heard", "why": "Neglecting a perspective", "relation": "" }]

```

Do **NOT** do this, ever:
```
[{"category": "distrust", "towards": "Johnny Depp", "why": "Negative association", "relation": ""}]
[{"category": "distrust", "towards": "Amber Heard", "why": "Negative association", "relation": ""}]
```

If an entity isn't JD or AH, describe their relation to JD or AH (if one can be deduced from the text):
```
[{ "category": "trust", "towards": "media", "why": "Fair and balanced", "relation": "Both are media personalities" }]
```

Ensure all characters in the JSON are properly escaped:
```
[{"category": "trust", "towards": "Amber Heard", "why": "Statement about \"properly escaped\"", "relation": ""}]
```

Ensure you always use double quotes in the JSON. Single quotes aren't valid JSON.
This is a valid response:
```
[{"category": "distrust", "towards": "Amber Heard", "why": "Criticizing or Blamin}]
```

And this is an **invalid** response (due to the use of single quotes):
```
[{'category': 'distrust', 'towards': 'Amber Heard', 'why': 'Pathetic attempt by AH team'}]
```

Always finish your JSON and return a complete array. Never end your response with an ellipsis. **This is BAD**: 
```
[{"category": "trust", "towards": "Ben and Jerry", "why": "Tasty icecream", "relation": ""}, 
{"category": "distrust", "towards": "Amber Heard", "why"...
```

Note that the only two valid options for the "category" attribute are "trust" and "distrust". 
Do not look for anything else, but look exhaustively.

Pydantic class definition for response validation:
```
class TrustIndicator(BaseModel):
    category: str
    towards: str
    why: str
    relation: str
```
Note that none of the attributes are optional.

Avoid sending any response other than the required JSON.

Be short and succinct in your replies and analyses.

Analyze the following text and find - at most - 10 indicators of trust. If you find more than one, put them all 
in one array when you respond:
""" + text

    response = get_chat_completion(system_prompt=system_prompt, prompt=prompt_text)
    try:
        result = []
        message = response.choices[0].message['content'].strip()
        if message[:2] == "**" and message[-2:] == "**":
            message = message[2:-2]
        indicators = json.loads(message)
        for indicator in indicators:
            result.append(TrustIndicator(**indicator))
        return result
    except Exception as e:
        print("An error occurred while parsing JSON:", e)
        message = response.choices[0].message['content'].strip()
        print(message)
        if message.count("'") > 1:
            print("Trying again with a method that supports single quoted JSON.")
            try:
                data = ast.literal_eval(message)
                for indicator in data:
                    result.append(TrustIndicator(indicator))
            except json.JSONDecodeError as e:
                print("Retry failed booooo")
                print(e)
                print(message)
        else:
            pattern = r'\[.*?\]'
            matches = re.findall(pattern, message)
            if len(matches) >= 2:
                print("Found two or more arrays, fixing and trying again...")
                combined_data = []
                for match in matches:
                    combined_data.extend(json.loads(match))
                for indicator in combined_data:
                    result.append(TrustIndicator(**indicator))

        return result


def get_processed_files():
    if os.path.exists("processed_files.log"):
        with open("processed_files.log", "r") as log_file:
            return log_file.read().splitlines()
    return []


def get_unprocessed_files(path):
    return sorted([os.path.join(path, f) for f in os.listdir(path) if f.endswith('.json')], key=os.path.getctime)


def load_analysis_from_file(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return [PostAnalysis(**post_data) for post_data in data]


def process_comments_recursive(comment_analysis):
    print(f"Analyzing comment: {comment_analysis.comment_text}")
    comment_analysis.trust_indicators = find_trust_indicators(comment_analysis.comment_text)
    print(f"Trust indicators: {comment_analysis.trust_indicators}")
    for reply in comment_analysis.comments:
        process_comments_recursive(reply)


def process_and_update_analysis(posts_analysis):
    for post_analysis in posts_analysis:
        print(f"Analyzing post: {post_analysis.post_title}")
        post_analysis.trust_indicators = find_trust_indicators(post_analysis.post_text)
        print(f"Trust indicators: {post_analysis.trust_indicators}")
        for comment_analysis in post_analysis.comments:
            process_comments_recursive(comment_analysis)


def save_analysis_to_file(posts_analysis, filename):
    with open(filename, 'w') as file:
        json.dump([p.model_dump() for p in posts_analysis], file, indent=4)
    print(f"Analysis saved to {filename}")


def log_processed_file(filename):
    with open("processed_files.log", "a") as log_file:
        log_file.write(filename + "\n")


def update_trust_indicators(path):
    files = get_unprocessed_files(path)
    processed_files = get_processed_files()
    for filename in files:
        if filename in processed_files:
            print(f"{filename} has already been processed. Skipping...")
            continue
        print(f"Processing file: {filename}")
        posts_analysis = load_analysis_from_file(filename)
        process_and_update_analysis(posts_analysis)
        save_analysis_to_file(posts_analysis, filename)  # Make sure to modify the save function
        log_processed_file(filename)


update_trust_indicators(path='D:\\data\\tilburguniversity\\inge\\trust')
