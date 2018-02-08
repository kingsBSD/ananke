#  sudo apt-get install linux-image-generic-lts-vivid linux-headers-generic-lts-vivid
# sudo apt-get remove linux-image-4.2.0-42-generic
apt-get update
apt-get install -q -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update
apt-get -q -y install docker-ce
usermod -aG docker $USER