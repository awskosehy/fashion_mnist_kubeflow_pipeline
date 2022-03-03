import kfp
import kfp.dsl as dsl
import requests
import os
import json
import config

from kfp import components
from kfp import onprem
from kubernetes.client.models import V1EnvVar

create_pytorchjob_fashion_mnist_katib_experiment_op = kfp.components.load_component_from_file(
    "/src/2_katib/component.yaml"
)
create_tensorboard_launcher_op = kfp.components.load_component_from_file(
    "/src/3_tensorboard/component.yaml"
)
create_model_path_launcher_op = kfp.components.load_component_from_file(
    "/src/4_model_path/component.yaml"
)

def extract_best_trial_name(katib_results) -> str:
    """ Extract the best trial name.
      
    Args:
    katib_results: The JSON object formatted the hyperparameter set of the best experiment trial result

    Returns:
    best_trial_name: string which contain the best experiment trial name
    """
    import json
    import pprint
    katib_results_json = json.loads(katib_results)
    best_trial_name = katib_results_json["currentOptimalTrial"]["bestTrialName"] + '-master-0'

    return best_trial_name


@dsl.pipeline(
    name=config.PIPELINE_NAME,
    description=config.DESCRIPTION
)

def create_pytorch_fashion_mnist_pipeline():
    fashion_mnist_katib_experiment = create_pytorchjob_fashion_mnist_katib_experiment_op(
        experiment_name=config.EXPERIMENT_NAME,
        experiment_namespace=config.EXPERIMENT_NAMESPACE,
        dataset_path=config.DATASET_PATH,
        log_dir=config.MODEL_DIR,
        max_trial_count=config.MAX_TRIAL_COUNT,
        max_failed_trial_count=config.MAX_FAILED_TRIAL_COUNT,
        parallel_trial_count=config.PARALLEL_TRIAL_COUNT,
        epochs=config.EPOCHS,
        loss_goal=config.LOSS_GOAL,
        min_learning_rate=config.MIN_LR,
        max_learning_rate=config.MAX_LR,
        min_momentum=config.MIN_MOMENTUM,
        max_momentum=config.MAX_MOMENTUM,
        pytorch_fashion_mnist_image=config.PYTORCH_FAHION_MNIST_IMAGE,
    )

    tensorboard_pipeline = create_tensorboard_launcher_op(
        s3_path = 's3://tensorboard' + config.LOG_DIR,
    ).apply(onprem.mount_pvc('minio-pvc-volume','minio-pv-volume','/workspace/minio')) \
    .add_env_variable(V1EnvVar(name='S3_ENDPOINT', value=config.S3_ENDPOINT)) \
    .add_env_variable(V1EnvVar(name='AWS_ENDPOINT_URL', value=config.AWS_ENDPOINT_URL)) \
    .add_env_variable(V1EnvVar(name='AWS_ACCESS_KEY_ID', value=config.AWS_ACCESS_KEY_ID)) \
    .add_env_variable(V1EnvVar(name='AWS_SECRET_ACCESS_KEY', value=config.AWS_SECRET_ACCESS_KEY)) \
    .add_env_variable(V1EnvVar(name='AWS_REGION', value=config.AWS_REGION)) \
    .add_env_variable(V1EnvVar(name='S3_USE_HTTPS', value='0')) \
    .add_env_variable(V1EnvVar(name='SE_VERIFY_SSL', value='0'))

    extract_best_trial_name_op =components.func_to_container_op(extract_best_trial_name)
    best_trial_name = extract_best_trial_name_op(
        fashion_mnist_katib_experiment.output
    ).after(fashion_mnist_katib_experiment)

    model_path = create_model_path_launcher_op(
        model_path = config.MINIO_ADDR + config.MINIO_PATH + str(best_trial_name.output) + '/'
    ).after(best_trial_name)

if __name__=="__main__":
    # resolve kfp_server_api.exceptions.ApiException: (400) NAMESPACE is empty issue
    os.system('mkdir -p ~/.config/kfp')
    context = {
        "namespace": "admin"
    }

    with open("context.json", "w") as write_file:
        json.dump(context, write_file)
    os.system('mv context.json ~/.config/kfp/context.json')
    
    pipeline_func = create_pytorch_fashion_mnist_pipeline

    session = requests.Session()
    response = session.get(config.HOST)

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {"login": config.USERNAME, "password": config.PASSWORD}
    session.post(response.url, headers=headers, data=data)
    print(session.cookies.get_dict())
    session_cookie = session.cookies.get_dict()["authservice_session"]

    print(f'session_cookie: {session_cookie}')

    from kubernetes import client as k8s_client
    pipeline_conf = kfp.dsl.PipelineConf()
    pipeline_conf.set_image_pull_secrets([k8s_client.V1ObjectReference(name="registry-credentials")])

    # Compile pipeline to generate compressed YAML definition of the pipeline.
    kfp_client=kfp.Client(
        host=f"{config.HOST}/pipeline",
        cookies=f"authservice_session={session_cookie}",
        namespace=config.NAMESPACE
    )
    run_id=kfp_client.create_run_from_pipeline_func(pipeline_func,
                                                    arguments={},
                                                    pipeline_conf=pipeline_conf,
                                                    )
 