import datetime
import json
import os
import re

from jinja2 import Environment, select_autoescape, FileSystemLoader
from markdown import markdown

exported_files_path = os.path.join(os.path.curdir, 'exported_files')


def get_channel_posts(users, channel_directory):
    posts = []
    channel_path = os.path.join(exported_files_path, channel_directory)
    for channel_item in os.listdir(channel_path):
        if not os.path.isfile(os.path.join(channel_path, channel_item)):
            continue

        with open(os.path.join(os.path.join(channel_path, channel_item))) as file:
            day_posts = json.load(file)

        for post in day_posts:
            if 'type' not in post or post['type'] != 'message' or 'subtype' in post:
                continue

            user_regex = '<@(U[^>]+)'
            message = post['text']
            for user_id in re.findall(user_regex, post['text']):
                if user_id in users:
                    message = message.replace(user_id, users[user_id]['profile']['real_name'])

            posts.append({
                'user': post['user'] in users and users[post['user']]['profile']['real_name'] or post['user'],
                'message': markdown(message),
                'timestamp': datetime.datetime.fromtimestamp(int(post['ts'].split('.')[0]))
            })

    return posts


def main():
    with open(os.path.join(exported_files_path, 'users.json')) as file:
        users = {u['id']: u for u in json.load(file)}

    template_env = Environment(
        loader=FileSystemLoader(os.path.join(os.path.curdir, 'templates')),
        autoescape=select_autoescape(['html', 'xml'])
    )

    output_directory = os.path.join(os.path.curdir, 'output')
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for directory_item in os.listdir(exported_files_path):
        if not os.path.isdir(os.path.join(exported_files_path, directory_item)):
            continue

        posts = sorted(get_channel_posts(users, directory_item), key=lambda post: post['timestamp'])

        template = template_env.get_template('channel_dump.html')
        html = template.render(posts=posts)

        file_path = os.path.join(output_directory, directory_item + '.html')
        if os.path.exists(file_path):
            os.remove(file_path)

        with open(file_path, 'w') as file:
            file.write(html)



if __name__ == '__main__':
    main()
