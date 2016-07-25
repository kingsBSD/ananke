#  sudo apt-get install linux-image-generic-lts-vivid linux-headers-generic-lts-vivid
# sudo apt-get remove linux-image-4.2.0-42-generic
apt-get update
apt-get install -q -y apt-transport-https ca-certificates
apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
echo 'deb https://apt.dockerproject.org/repo ubuntu-xenial main' > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get -q -y install linux-image-extra-$(uname -r)
apt-get -q -y install docker-engine
