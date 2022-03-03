import json
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description='Parse minio location from \
                                              kubeflow pipeline')
parser.add_argument("--model-path",
                    default="",
                    type=str,
                    help="model path[Required]")
parser.add_argument('--ui-metadata-output-path',
                    default='/mlpipeline-metrics.json',
                    type=str,
                    help='MLPipeline Metrics')
# Parser arguments
args = parser.parse_args()
print(f'args: {args}')
metadata = {
    'outputs' :[{
        'storage': 'inline',
        'source': '# model path\n [A link]('+args.model_path+')',
        'type': 'markdown',
    }]
}
Path(args.ui_metadata_output_path).parent.mkdir(parents=True, exist_ok=True)
Path(args.ui_metadata_output_path).write_text(json.dumps(metadata))