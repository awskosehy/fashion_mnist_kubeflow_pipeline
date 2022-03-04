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
kubectl apply -f https://openebs.github.io/charts/nfs-operator.yaml
```