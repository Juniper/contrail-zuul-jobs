#!/usr/bin/python
from __future__ import print_function
import subprocess as sub
import json

image_ids = sub.check_output(["docker", "images", "--format", "{{ .ID }}"])
image_ids = set(image_ids.splitlines())

data = {}

for image_id in image_ids:
    image_json = sub.check_output(["docker", "inspect", image_id])
    image = json.loads(image_json)[0]
    tags = image["RepoTags"]
    if len(tags) > 1:
        print("Expecting only one tag per image, got:", len(tags))
    for tag in tags:
        image_name = tag.split('/')[-1]
        data[image_name] = {'id': image['Id']}

data_json = json.dumps(data, indent=4)
print(data_json)

with open('docker_images.json', 'w') as outfile:
    outfile.write(data_json)
