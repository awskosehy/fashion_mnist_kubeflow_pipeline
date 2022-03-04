## setup kubeflow 1.2 dex version
### install kfctl
```
# during reinstall the kubeflow make another clone cluster for testing purpose
sudo wget https://github.com/kubeflow/kfctl/releases/download/v1.2.0/kfctl_v1.2.0-0-gbc038f9_linux.tar.gz &&
sudo tar -zxvf kfctl_v1.2.0-0-gbc038f9_linux.tar.gz &&
sudo mv kfctl /usr/bin/
```

### install kubeflow 1.2 dex
```
export BASE_DIR=/home/ubuntu
export KF_NAME=kubeflow-install
# Set the path to the base directory where you want to store one or more
# Kubeflow deployments. For example, /opt/.
# Then set the Kubeflow application directory for this deployment.
export KF_DIR=${BASE_DIR}/${KF_NAME}

# Set the configuration file to use when deploying Kubeflow.
# The following configuration installs Istio by default. Comment out
# the Istio components in the config file to skip Istio installation.
# See https://github.com/kubeflow/kubeflow/pull/3663
# export CONFIG_URI="https://raw.githubusercontent.com/kubeflow/manifests/v1.2-branch/kfdef/kfctl_k8s_istio.v1.2.0.yaml"
mkdir -p ${KF_DIR}
cd ${KF_DIR}
export CONFIG_URI="https://raw.githubusercontent.com/kubeflow/manifests/v1.2-branch/kfdef/kfctl_istio_dex.v1.2.0.yaml"

wget -O kfctl_istio_dex.yaml ${CONFIG_URI}
export CONFIG_FILE=${KF_DIR}/kfctl_istio_dex.yaml

kfctl apply -V -f ${CONFIG_FILE}
```
### access to kubeflow dashboard
```
https://PUBLIC_IP_ADDR:31380
```
### tensorboard minio setup
#### change minio-service type as NodePort
```
kubectl edit svc/minio-service -n kubeflow
```
go to minio browser

create "tensorboard" bucket


create "mlpipeline" bucket

create "mlpipeline/pipelines" forlder

create "mlpipeline/artifacts" forlder

### create ml-pipeline-aws-secret
```
export AWS_ACCESS_KEY_ID=minio
export AWS_SECRET_ACCESS_KEY=minio123
kubectl -n admin create secret generic ml-pipeline-aws-secret \
    --from-literal=accesskey=$AWS_ACCESS_KEY_ID \
    --from-literal=secretkey=$AWS_SECRET_ACCESS_KEY
```

### viewer-tensorboard-template.yaml
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: ml-pipeline-ui-viewer-template
data:
  viewer-tensorboard-template.json: |
    {
        "spec": {
            "containers": [
                {
                    "env": [
                        {
                            "name": "AWS_ACCESS_KEY_ID",
                            "valueFrom": {
                                "secretKeyRef": {
                                    "name": "ml-pipeline-aws-secret",
                                    "key": "accesskey"
                                }
                            }
                        },
                        {
                            "name": "AWS_SECRET_ACCESS_KEY",
                            "valueFrom": {
                                "secretKeyRef": {
                                    "name": "ml-pipeline-aws-secret",
                                    "key": "secretkey"
                                }
                            }
                        },
                        {
                            "name": "S3_ENDPOINT",
                            "value": "minio-service.kubeflow.svc.cluster.local:9000"
                        },
                        {
                            "name": "AWS_ENDPOINT_URL",
                            "value": "<http://minio-service.kubeflow.svc.cluster.local:9000>"
                        },
                        {
                            "name": "AWS_REGION",
                            "value": "us-east-1"
                        },
                        {
                            "name": "S3_USE_HTTPS",
                            "value": "0"
                        },
                        {
                            "name": "S3_VERIFY_SSL",
                            "value": "0"
                        }
                    ]
                }
            ]
        }
    }
```

#### apply viewer-tensorboard-template.yaml
```
kubectl apply -f viewer-tensorboard-template.yaml -n kubeflow
```

#### update ml-pipeline-ui deployment config
```
KUBE_EDITOR=nano kubectl -n kubeflow edit deployment ml-pipeline-ui

spec:
      containers:
      - env:
        - name: VIEWER_TENSORBOARD_POD_TEMPLATE_SPEC_PATH
          value: /etc/config/viewer-pod-template.json
          ->          
          value: /etc/config/viewer-tensorboard-template.json
          
          
      volumes:
      - configMap:
          defaultMode: 420
          name: ml-pipeline-ui-configmap
          ->
          name: ml-pipeline-ui-viewer-template
```

### katib
#### fix x509: certificate relies on legacy Common Name field
create three files: ca-csr.json, server-csr.json, ca-config.json
#### ca-csr.json
```
{
    "CN": "katib-controller.kubeflow.svc",
    "hosts": [
        "katib-controller.kubeflow.svc"
    ],
    "key": {
        "algo": "ecdsa",
        "size": 256
    },
    "names": [
        {
            "C": "US",
            "ST": "CA",
            "L": "San Francisco"
        }
    ]
}
```
#### server-csr.json
```
{
    "CN":"katib-controller.kubeflow.svc",
    "hosts":[
        "katib-controller.kubeflow.svc"
    ],
    "key":{
        "algo":"rsa",
        "size":2048
    },
    "names":[
        {
            "C":"US",
            "L":"CA",
            "ST":"San Francisco"
        }
    ]
}
```
#### ca-config.json
```
{
    "signing": {
        "default": {
            "expiry": "168h"
        },
        "profiles": {
            "www": {
                "expiry": "8760h",
                "usages": [
                    "signing",
                    "key encipherment",
                    "server auth"
                ]
            },
            "client": {
                "expiry": "8760h",
                "usages": [
                    "signing",
                    "key encipherment",
                    "client auth"
                ]
            },
            "kubernetes": {
                "expiry": "876000h",
                "usages": [
                    "signing",
                    "key encipherment",
                    "server auth",
                    "client auth"
                    ]
            }
        }
    }
}
```
#### refresh k8s secret
##### Download cfssl
```
sudo wget https://github.com/cloudflare/cfssl/releases/download/v1.6.0/cfssl_1.6.0_linux_amd64
sudo chmod +x cfssl_1.6.0_linux_amd64
sudo mv cfssl_1.6.0_linux_amd64 cfssl
sudo mv cfssl /usr/bin
```
##### Download cfssljson
```
sudo wget https://github.com/cloudflare/cfssl/releases/download/v1.6.0/cfssljson_1.6.0_linux_amd64
sudo chmod +x cfssljson_1.6.0_linux_amd64
sudo mv cfssljson_1.6.0_linux_amd64 cfssljson
sudo mv cfssljson /usr/bin
```
##### Generating SSL certs
```
cfssl gencert -initca ca-csr.json | cfssljson -bare ca –
cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes server-csr.json | cfssljson -bare server
```
##### Needed renaming
```
mv ca.pem ca-cert.pem
mv server.pem cert.pem
mv server-key.pem key.pem
```
##### k8s secret refresh
```
kubectl delete secret -n kubeflow katib-controller
kubectl create secret -n kubeflow generic katib-controller --from-file=ca-cert.pem --from-file=ca-key.pem --from-file=cert.pem --from-file=key.pem
kubectl get pod -n kubeflow | grep katib
```
##### Check the katib-controller pod name and then
```
kubectl get pod -n kubeflow | grep katib-controller | awk {'print $1'} | xargs kubectl delete pod -n kubeflow
```
### setup read write many(rwx) pv, pvc for minio deployment
#### minio_pv_rwx.yaml
```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: minio-pv-rwx
  namespace: kubeflow
spec:
  storageClassName: openebs-rwx
  capacity:
    storage: 100Gi
  accessModes:
  - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  local:
    path: /data
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - NODE_NAME
```
#### minio_pvc_rwx.yaml
```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: minio-pvc-rwx
  namespace: kubeflow
spec:
  storageClassName: openebs-rwx
  volumeName: minio-pv-rwx
  accessModes:
  - ReadWriteMany
  resources:
    requests:
      storage: 100Gi
```
#### apply minio_pv_rwx, minio_pvc_rwx
```
kubectl apply -f minio_pv_rwx.yaml -f minio_pvc_rwx.yaml
```
#### update minio deployment config
```
KUBE_EDITOR=nano kubectl edit deploy/minio -n kubeflow

volumes":[{"name":"data","persistentVolumeClaim":{"claimName":"minio-pvc -> minio-pvc-rwx"}

spec:
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: minio-pvc -> minio-pvc-rwx
```
### install kubernetes dahsboard for debugging
```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.5.0/aio/deploy/recommended.yaml
```
#### create sample user in k8s dashboard
```
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
EOF

cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kubernetes-dashboard
EOF

kubectl -n kubernetes-dashboard get secret $(kubectl -n kubernetes-dashboard get sa/admin-user -o jsonpath="{.secrets[0].name}") -o go-template="{{.data.token | base64decode}}"
```
#### change kubernetes-dashboard svc as NodePort
```
kubectl -n kubernetes-dashboard edit svc/kubernetes-dashboard
```
#### check kubernetes-dashboard nodeport
```
kubectl -n kubernetes-dashboard get svc/kubernetes-dashboard
```

#### how to access kubernetes-dashboard
```
https://PUBLIC_IP://KUBERNETES-DASHBOARD-NODEPORT
```
### prepare fashion-mnist kubeflow pipeline
#### change pv's nodeAffinity values
```
kubectl apply -f minio_pv_admin.yaml -f minio_pvc_admin.yaml -f storage_pv.yaml -f storage_pvc.yaml
```
#### make folder /data/storage
#### change config.py
#### build docker images
```
sh build.sh
```
#### run kfp docker ocntainer
```
docker run -it --rm kosehy/kfp
```
#### run the pipeline.py
```
python pipeline.py
```