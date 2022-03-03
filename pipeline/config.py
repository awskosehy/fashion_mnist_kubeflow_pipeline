# pipeline parameters
DESCRIPTION='add save a general checkpoint for inference and/or resuming training'
PROJECT_NAME = 'pytorchjob-katib'
PIPELINE_NAME = PROJECT_NAME + '-pipeline'
EXPERIMENT_VERSION = 'v005'
EXPERIMENT_NAME = PIPELINE_NAME + '-' + EXPERIMENT_VERSION
EXPERIMENT_NAMESPACE = 'admin'
NAME = EXPERIMENT_NAME
DATASET_PATH = '/workspace/project/' + PROJECT_NAME + '/model/data/'
RANDOM_HOSTNAME = '/' + '$(cat /etc/hostname)'
MODEL_DIR = '/workspace/minio/tensorboard/project/' + PROJECT_NAME + '/model/' + NAME + '/'
MODEL_DIR_WITH_HOST = MODEL_DIR + RANDOM_HOSTNAME
LOG_DIR = '/project/' + PROJECT_NAME + '/model/' + NAME + '/'
MINIO_PATH = 'minio/tensorboard/project/' + PROJECT_NAME + '/model/' + NAME + '/'
IP_ADDRESS = '34.216.158.83'

# minio parameters
S3_ENDPOINT = 'minio-service.kubeflow.svc.cluster.local:9000'
AWS_ENDPOINT_URL = "http://" + S3_ENDPOINT
AWS_ACCESS_KEY_ID = "minio"
AWS_SECRET_ACCESS_KEY = "minio123"
AWD_REGION = "us-east-1"
MINIO_ADDR = 'http://' + IP_ADDRESS + ':31279/'

# katib parameters
MAX_TRIAL_COUNT = 1
MAX_FAILED_TRIAL_COUNT = 4
PARALLEL_TRIAL_COUNT = 1
EPOCHS = 10
LOSS_GOAL = 0.001
MIN_LR = 0.01
MAX_LR = 0.05
MIN_MOMENTUM = 0.5
MAX_MOMENTUM = 0.9
PYTORCH_FAHION_MNIST_IMAGE = 'kosehy/katib_pytorchjob:latest'

# auth info
USERNAME = "admin@kubeflow.org"
PASSWORD = "12341234"
NAMESPACE = 'admin'
HOST = 'http://' + IP_ADDRESS + ':31380'