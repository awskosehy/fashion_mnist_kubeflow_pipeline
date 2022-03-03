# fashion mnisht pytorch kubeflow pipeline
1. select g4dn.2xlarge
2. storage: 50GB
3. open all TCP port
4. 


# how to setup k8s

## set ubuntu password
```
sudo passwd ubuntu
```

## install apt packages
```
sudo apt-get update
sudo apt-get install -y socat
```

## install docker
### install apt packages for docker
```
sudo apt-get update && sudo apt-get install -y ca-certificates curl gnupg lsb-release
```

### add docker official GPG key
```
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
```

### set docker stable repository
```
echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
$(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### check available docker version
```
sudo apt-get update && apt-cache madison docker-ce
```

### install 5:20.10.11-3-0-ubuntu-focal docker
```
sudo apt-get install -y containerd.io docker-ce=5:20.10.11~3-0~ubuntu-focal docker-ce-cli=5:20.10.11~3-0~ubuntu-focal
```

### add ubuntu as docker group
```
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

### change network for kubernetes
```
sudo modprobe br_netfilter

cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
br_netfilter
EOF

cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF
sudo sysctl --system
```

### install package for kubeadm, kubelet, kubectl 1.19.16
```
sudo apt-get update && sudo apt-get install -y apt-transport-https curl
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add - 
cat <<EOF | sudo tee /etc/apt/sources.list.d/kubernetes.list
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF
sudo apt-get update
```

### install kubeadm, kubelet, kubectl 1.19.16
```
sudo apt-get install -y kubelet=1.19.16-00 kubeadm=1.19.16-00 kubectl=1.19.16-00 &&
sudo apt-mark hold kubelet kubeadm kubectl
```

### check kubernetes version
```
kubeadm version
kubelet --version
kubectl version
```

### install kubernetes using kubeadm
```
kubeadm config images list
kubeadm config images pull

sudo kubeadm init --pod-network-cidr=10.244.0.0/16
```

### copy admin certificate for kubernetes cluster
```
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### install calico
```
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
```

### taint nodes for master node to do any work
```
kubectl taint nodes --all node-role.kubernetes.io/master-
```

### configure kubelet
```
KUBE_EDITOR="nano" kubectl edit configmap/kubelet-config-1.19 -n kube-system

# add two codes

container-runtime: docker
image-pull-progress-deadline: 10m
```

### configure kube-apiserver
```
sudo nano /etc/kubernetes/manifests/kube-apiserver.yaml

# add two codes
- --service-account-issuer=kubernetes.default.svc
- --service-account-signing-key-file=/etc/kubernetes/pki/sa.key
```

### restart kubelet
```
systemctl restart kubelet
```

### install helm
```
wget https://get.helm.sh/helm-v3.7.1-linux-amd64.tar.gz
tar -zxvf helm-v3.7.1-linux-amd64.tar.gz
sudo mv linux-amd64/helm /usr/local/bin/helm
```

### install nvidia driver
```
sudo add-apt-repository ppa:graphics-drivers/ppa &&
sudo apt update &&
sudo apt install -y ubuntu-drivers-common &&
sudo ubuntu-drivers autoinstall &&
sudo reboot
```

### install nvidia docker
```
# install nvidia docker
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | \
  sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
```
```
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
```
```
sudo apt-get update &&
sudo apt-get install -y nvidia-docker2 &&
sudo systemctl restart docker
```

### set the nvidia-docker as container's default runtime
```
sudo nano /etc/docker/daemon.json
```
```

{
  "default-runtime": "nvidia",
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}
```

### restart docker
```
sudo systemctl daemon-reload
sudo service docker restart
```

### check docker
```
sudo docker info | grep nvidia
```

### install nvidia device plugin
```
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.10.0/nvidia-device-plugin.yml
sleep 30s
kubectl get pod -n kube-system | grep nvidia
sleep 10s
kubectl get nodes "-o=custom-columns=NAME:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu"
```
### install openebs
```
helm repo add openebs https://openebs.github.io/charts
helm repo update
helm install openebs --namespace openebs openebs/openebs --create-namespace
```
##### openebs install verification
```
kubectl get pods -n openebs -l openebs.io/component-name=openebs-localpv-provisioner
# sleep 1 minute
sleep 90s
# change default storage class as openebs-hostpath
kubectl patch storageclass openebs-hostpath -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```
### install openebs nfs provisioner
```
helm repo add openebs https://openebs.github.io/charts
helm repo update
helm install openebs openebs/openebs -n openebs --create-namespace --set nfs-provisioner.enabled=true
```
#### openebs_rwx_sc.yaml
```
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: openebs-rwx
  annotations:
    openebs.io/cas-type: nfsrwx
    cas.openebs.io/config: |
      - name: NFSServerType
        value: "kernel"
      - name: BackendStorageClass
        value: "openebs-hostpath"
      #  LeaseTime defines the renewal period(in seconds) for client state
      #- name: LeaseTime
      #  value: 30
      #  GraceTime defines the recovery period(in seconds) to reclaim locks
      #- name: GraceTime
      #  value: 30
      #  FSGID defines the group permissions of NFS Volume. If it is set
      #  then non-root applications should add FSGID value under pod
      #  Supplemental groups
      #- name: FSGID
      #  value: "120"
provisioner: openebs.io/nfsrwx
reclaimPolicy: Delete
```

### apply openebs_rwx_sc
```
kubectl apply -f openebs_rwx_sc.yaml
```

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

### tensorboard minio setup
#### change minio-service type as NodePort
```
kubectl edit svc/minio-service -n kubeflow
```
go to minio browser
create "tensorboard" bucket

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
mv cfssl_1.6.0_linux_amd64 cfssl
sudo mv cfssl /usr/bin
```
##### Download cfssljson
```
sudo wget https://github.com/cloudflare/cfssl/releases/download/v1.6.0/cfssljson_1.6.0_linux_amd64
sudo chmod +x cfssljson_1.6.0_linux_amd64
mv cfssljson_1.6.0_linux_amd64 cfssljson
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
          - k8s
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
