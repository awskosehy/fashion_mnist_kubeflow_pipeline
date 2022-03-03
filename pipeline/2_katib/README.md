## pytorchjob fashion mnist katib pipeline

## How to make docker environment
```
docker run -it \
-v /data/storage:/workspace/storage \
-v /data/minio:/workspace/minio \
kosehy/katib_pytorchjob:test \
/bin/bash
```
