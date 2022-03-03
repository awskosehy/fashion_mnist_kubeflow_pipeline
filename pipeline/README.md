```
docker run -it \
-v /data/minio:/app/minio \
-v /data/storage:/app/storage \
kosehy/kfp:latest /bin/bash
```