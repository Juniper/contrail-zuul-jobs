#!/usr/bin/python
from __future__ import print_function
import sys
import subprocess as sub
import json
import re

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--name-filter-regex", type=str, default='.*')
parser.add_argument("--tag-filter-regex", type=str, default='.*')
args = parser.parse_args()

name_filter_regex = re.compile(args.name_filter_regex)
tag_filter_regex = re.compile(args.tag_filter_regex)

image_ids = sub.check_output(["docker", "images", "--format", "{{ .ID }}"])
image_ids = set(image_ids.splitlines())

container_images = {}

for image_id in image_ids:
    image_json = sub.check_output(["docker", "inspect", image_id])
    image = json.loads(image_json)[0]
    # "RepoTags" contains full image paths (1.2.3.4:5000/ns/image:tag)
    fqdns = image["RepoTags"]
    if len(fqdns) > 1:
        print("Expecting only one tag per image, got:", len(fqdns))
    for fqdn in fqdns:
        image_name = fqdn.split('/')[-1]
        image_name, image_tag = image_name.split(':')
        if (name_filter_regex.search(image_name) and
                tag_filter_regex.search(image_tag)):
            if image_name not in container_images:
                container_images[image_name] = {}
            container_images[image_name][image_tag] = {'id': image['Id']}

data = {'artifacts': {'container_images': container_images}}
data_json = json.dumps(data, indent=4)
print(data_json)

with open('docker_images.json', 'w') as outfile:
    outfile.write(data_json)
