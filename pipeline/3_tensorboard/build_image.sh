#!/bin/bash -e
image_name=kosehy/kfp_tensorboard
image_tag=latest
full_image_name=${image_name}:${image_tag}

echo "Releasing image for the tensorboard Pipeline Launcher..."
echo -e "Image: "${full_image_name}"\n"

docker build -t "${full_image_name}" .
docker push "${full_image_name}"

# Output the strict image name (which contains the sha256 image digest)
docker inspect --format="{{index .RepoDigests 0}}" "${full_image_name}"