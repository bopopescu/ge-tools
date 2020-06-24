search='127.0.0.1'
k3smaster='10.11.11.2'
kubecfg=~/.kube/k3s-$k3smaster.yaml
if [ ! -f "$kubecfg" ]; then
  echo "get kube config"
  scp rancher@$k3smaster:/etc/rancher/k3s/k3s.yaml ~/.kube/k3s-$k3smaster.yaml
  sed -i "s!$search!$k3smaster!g" ~/.kube/k3s-$k3smaster.yaml
fi
export KUBECONFIG=~/.kube/k3s-$k3smaster.yaml
echo "export KUBECONFIG=~/.kube/k3s-$k3smaster.yaml"
PS1='\[\e]0;\u@\h: \w\a\]${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\](11)\$ '
