from __future__ import absolute_import, division, print_function, unicode_literals
import argparse
import json
import tensorflow as tf
from pathlib import Path

def tensorboard_display():
    parser = argparse.ArgumentParser()
    parser.add_argument('--s3-path',
                        default='./data/logs',
                        type=str)
    parser.add_argument('--ui-metadata-output-path',
                        default='/mlpipeline-ui-metadata.json',
                        type=str)
    args = parser.parse_args()
    print(f'args.s3_path: {args.s3_path}')
    print("TensorFlow version: ", tf.__version__)
    metadata = {
        'outputs': [{
            'type': 'tensorboard',
            'source': args.s3_path,
        }]
    }
    Path(args.ui_metadata_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(args.ui_metadata_output_path).write_text(json.dumps(metadata))
if __name__ == '__main__':
    tensorboard_display()