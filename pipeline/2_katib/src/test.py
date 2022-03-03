# Copyright 2020 The Kubeflow Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import datetime
from distutils.util import strtobool
import json
import os
import logging
import time

from kubernetes.client import V1ObjectMeta

from kubeflow.katib import KatibClient
from kubeflow.katib import ApiClient
from kubeflow.katib import V1beta1Experiment
from kubeflow.katib import V1beta1ExperimentSpec
from kubeflow.katib import V1beta1AlgorithmSpec
from kubeflow.katib import V1beta1EarlyStoppingSpec
from kubeflow.katib import V1beta1EarlyStoppingSetting
from kubeflow.katib import V1beta1ObjectiveSpec
from kubeflow.katib import V1beta1MetricStrategy
from kubeflow.katib import V1beta1ParameterSpec
from kubeflow.katib import V1beta1FeasibleSpace
from kubeflow.katib import V1beta1MetricsCollectorSpec
from kubeflow.katib import V1beta1CollectorSpec
from kubeflow.katib import V1beta1SourceSpec
from kubeflow.katib import V1beta1FilterSpec
from kubeflow.katib import V1beta1FileSystemPath
from kubeflow.katib import V1beta1TrialTemplate
from kubeflow.katib import V1beta1TrialParameterSpec

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

FINISH_CONDITIONS = ["Succeeded", "Failed"]


class JSONObject(object):
    """ This class is needed to deserialize input JSON.
    Katib API client expects JSON under .data attribute.
    """

    def __init__(self, json):
        self.data = json

def wait_experiment_finish(katib_client, experiment, timeout):
    polling_interval = datetime.timedelta(seconds=30)
    end_time = datetime.datetime.now() + datetime.timedelta(minutes=timeout)
    experiment_name = experiment.metadata.name
    experiment_namespace = experiment.metadata.namespace
    while True:
        current_status = None
        try:
            current_status = katib_client.get_experiment_status(name=experiment_name, namespace=experiment_namespace)
        except Exception as e:
            logger.info("Unable to get current status for the Experiment: {} in namespace: {}. Exception: {}".format(
                experiment_name, experiment_namespace, e))
        # If Experiment has reached complete condition, exit the loop.
        if current_status in FINISH_CONDITIONS:
            logger.info("Experiment: {} in namespace: {} has reached the end condition: {}".format(
                experiment_name, experiment_namespace, current_status))
            return
        # Print the current condition.
        logger.info("Current condition for Experiment: {} in namespace: {} is: {}".format(
            experiment_name, experiment_namespace, current_status))
        # If timeout has been reached, rise an exception.
        if datetime.datetime.now() > end_time:
            raise Exception("Timout waiting for Experiment: {} in namespace: {} "
                            "to reach one of these conditions: {}".format(
                                experiment_name, experiment_namespace, FINISH_CONDITIONS))
        # Sleep for poll interval.
        time.sleep(polling_interval.seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Katib Experiment launcher')
    parser.add_argument('--experiment-name', type=str, default='',
                        help='Experiment name')
    parser.add_argument('--experiment-namespace', type=str, default='admin',
                        help='Experiment namespace')
    parser.add_argument("--dataset-path", type=str, default="./data",
                        help="Dataset path")
    parser.add_argument("--log-dir", type=str, default='',
                        help="Path to save summary writer logs.")
    parser.add_argument('--max-trial-count', type=int, default=1,
                        help='Number of Max trial count')
    parser.add_argument('--max-failed-trial-count', type=int, default=1,
                        help='Number of Max failed trial allowed')
    parser.add_argument('--parallel-trial-count', type=int, default=1,
                        help='Number of parallel katib job want to run')
    parser.add_argument('--loss-goal', type=float, default=0.90,
                        help='Goal of loss value to achieve during katib')
    parser.add_argument('--epochs', type=int, default=10, metavar="N",
                        help='number of epochs to train (default: 10)')
    parser.add_argument('--min-learning-rate', type=float, default=0.01,
                        help='Min Learning Rate value')
    parser.add_argument('--max-learning-rate', type=float, default=0.05,
                        help='Max Learning Rate value')
    parser.add_argument('--min-momentum', type=float, default=0.5,
                        help='Min Momentum value')
    parser.add_argument('--max-momentum', type=float, default=0.9,
                        help='Max Momentum value')
    parser.add_argument('--experiment-timeout-minutes', type=int, default=60*24*20,
                        help='Time in minutes to wait for the Experiment to complete')
    parser.add_argument('--delete-after-done', type=strtobool, default=False,
                        help='Whether to delete the Experiment after it is finished')
    parser.add_argument('--pytorch-fashion-mnist-image', type=str, default='kosehy/pytorch_fashion_mnist:latest',
                        help='Which Docker Container Image is used for pytorch fashion mnist')
    parser.add_argument('--output-file', type=str, default='/output.txt',
                        help='The file which stores the best hyperparameters of the Experiment')

    args = parser.parse_args()

    experiment_name = args.experiment_name
    experiment_namespace = args.experiment_namespace
    dataset_path = args.dataset_path
    log_dir = args.log_dir
    max_trial_count = str(args.max_trial_count)
    max_failed_trial_count = str(args.max_failed_trial_count)
    parallel_trial_count = str(args.parallel_trial_count)
    loss_goal = str(args.loss_goal)
    epochs = str(args.epochs)
    min_learning_rate = str(args.min_learning_rate)
    max_learning_rate = str(args.max_learning_rate)
    min_momentum = str(args.min_momentum)
    max_momentum = str(args.max_momentum)
    delete_after_done = args.delete_after_done
    pytorch_fashion_mnist_image = str(args.pytorch_fashion_mnist_image)

    experiment_spec = {
        "algorithm":{
            "algorithmName":"random"
        },
        "maxFailedTrialCount":max_failed_trial_count,
        "maxTrialCount":max_trial_count,
        "objective":{
            "goal":loss_goal,
            "objectiveMetricName":"loss",
            "type":"minimize"
        },
        "parallelTrialCount":parallel_trial_count,
        "parameters":[
            {
                "feasibleSpace":{
                    "min":min_learning_rate,
                    "max":max_learning_rate
                },
                "name":"lr",
                "parameterType":"double"
            },
            {
                "feasibleSpace":{
                    "min":min_momentum,
                    "max":max_momentum
                },
                "name":"momentum",
                "parameterType":"double"
            }
        ],
        "trialTemplate":{
            "primaryContainerName":"pytorch",
            "retain":"true",
            "trialParameters":[
                {
                    "description":"Learning Rate",
                    "name":"learningRate",
                    "reference":"lr"
                },
                {
                    "description":"Momentum",
                    "name":"momentum",
                    "reference":"momentum"
                }
            ],
            "trialSpec":{
                "apiVersion":"kubeflow.org/v1",
                "kind":"PyTorchJob",
                "spec":{
                    "pytorchReplicaSpecs":{
                        "Master":{
                            "replicas":1,
                            "restartPolicy":"ExitCode",
                            "template":{
                                "metadata":{
                                    "annotations":{
                                    "sidecar.istio.io/inject":"false"
                                    }
                                },
                                "spec":{
                                    "containers":[
                                        {
                                            "name":"pytorch",
                                            "image":pytorch_fashion_mnist_image,
                                            "command":[
                                                "python3",
                                                "src/fashion_mnist.py",
                                                "--dataset-path=" + dataset_path,
                                                "--log-dir=" + log_dir,
                                                "--epochs=" + epochs,
                                                "--lr=${trialParameters.learningRate}",
                                                "--momentum=${trialParameters.momentum}"
                                            ],
                                            "resources":{
                                                "limits":{
                                                    "nvidia.com/gpu":"1"
                                                }
                                            },
                                            "volumeMounts":[
                                                {
                                                    "mountPath":"/workspace/project",
                                                    "name":"project-pv-volume"
                                                },
                                                {
                                                    "mountPath":"/workspace/minio",
                                                    "name":"minio-rwx-pv-admin"
                                                }
                                            ]
                                        }
                                    ],
                                    "imagePullSecrets":[
                                        {
                                            "name":"registry-credentials",
                                        }
                                    ],
                                    "volumes":[
                                        {
                                            "name":"project-pv-volume",
                                            "persistentVolumeClaim":{
                                                "claimName":"project-pvc-volume"
                                            }
                                        },
                                        {
                                            "name":"minio-rwx-pv-admin",
                                            "persistentVolumeClaim":{
                                                "claimName":"minio-rwx-pvc-admin"
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    
    # Create JSON dump from experiment spec
    experiment_spec = json.dumps(experiment_spec)
    # Create JSON object from experiment spec
    experiment_spec = JSONObject(experiment_spec)
    # Deserialize JSON to ExperimentSpec
    experiment_spec = ApiClient().deserialize(experiment_spec, "V1beta1ExperimentSpec")

    # Create Experiment object.
    experiment = V1beta1Experiment(
        api_version="kubeflow.org/v1beta1",
        kind="Experiment",
        metadata=V1ObjectMeta(
            name=experiment_name,
            namespace=experiment_namespace
        ),
        spec=experiment_spec
    )

    # Print experiment
    print(f'experiment:{experiment}')
    # Create Katib client.
    katib_client = KatibClient()
    # Create Experiment in Kubernetes cluster.
    output = katib_client.create_experiment(experiment, namespace=experiment_namespace)

    # Wait until Experiment is created.
    end_time = datetime.datetime.now() + datetime.timedelta(minutes=args.experiment_timeout_minutes)
    while True:
        current_status = None
        # Try to get Experiment status.
        try:
            current_status = katib_client.get_experiment_status(name=experiment_name, namespace=experiment_namespace)
        except Exception:
            logger.info("Waiting until Experiment is created...")
        # If current status is set, exit the loop.
        if current_status is not None:
            break
        # If timeout has been reached, rise an exception.
        if datetime.datetime.now() > end_time:
            raise Exception("Timout waiting for Experiment: {} in namespace: {} to be created".format(
                experiment_name, experiment_namespace))
        time.sleep(1)

    logger.info("Experiment is created")

    # Wait for Experiment finish.
    wait_experiment_finish(katib_client, experiment, args.experiment_timeout_minutes)

    # Check if Experiment is successful.
    if katib_client.is_experiment_succeeded(name=experiment_name, namespace=experiment_namespace):
        logger.info("Experiment: {} in namespace: {} is successful".format(
            experiment_name, experiment_namespace))

        optimal_hp = katib_client.get_optimal_hyperparameters(
            name=experiment_name, namespace=experiment_namespace)
        logger.info(f'Optimal hyperparameters:\n{optimal_hp}')
        # Check output_file path
        logger.info(f'args.output_file:\n{args.output_file}')
        # Create dir if it doesn't exist.
        if not os.path.exists(os.path.dirname(args.output_file)):
            os.makedirs(os.path.dirname(args.output_file))
        # Save HyperParameters to the file.
        with open(args.output_file, 'w') as f:
            f.write(json.dumps(optimal_hp))
    else:
        logger.info("Experiment: {} in namespace: {} is failed".format(
            experiment_name, experiment_namespace))
        # Print Experiment if it is failed.
        experiment = katib_client.get_experiment(name=experiment_name, namespace=experiment_namespace)
        logger.info(experiment)

    # Delete Experiment if it is needed.
    if delete_after_done:
        katib_client.delete_experiment(name=experiment_name, namespace=experiment_namespace)
        logger.info("Experiment: {} in namespace: {} has been deleted".format(
            experiment_name, experiment_namespace))