#!/bin/bash
set -x
cd ${BASE_DIR}/openstack-helm
bash tools/deployment/developer/00-install-packages.sh
bash tools/deployment/developer/01-deploy-k8s.sh
#Build all helm charts and intll openstack and heat client
bash tools/deployment/developer/02-setup-client.sh
#Deploy openstack-helm related charts
bash tools/deployment/developer/03-ingress.sh
bash tools/deployment/developer/04-ceph.sh
bash tools/deployment/developer/05-ceph-ns-activate.sh
bash tools/deployment/developer/06-mariadb.sh
bash tools/deployment/developer/07-rabbitmq.sh
bash tools/deployment/developer/08-memcached.sh
bash tools/deployment/developer/09-keystone.sh
bash tools/deployment/developer/10-ceph-radosgateway.sh
bash tools/deployment/developer/11-horizon.sh
bash tools/deployment/developer/12-glance.sh
bash tools/deployment/developer/14-libvirt.sh
#Now deploy opencontrail charts
cd $CHD_PATH
make
kubectl label node opencontrail.org/controller=enabled --all
kubectl replace -f ${OSH_PATH}/tools/kubeadm-aio/assets/opt/rbac/dev.yaml
helm install --name contrail-thirdparty ${CHD_PATH}/contrail-thirdparty \
	--namespace=openstack --set contrail_env.CONTROLLER_NODES=${CONTROLLER_NODE} \
	--set manifests.each_container_is_pod=true
helm install --name contrail-controller ${CHD_PATH}/contrail-controller \
	--namespace=openstack --set contrail_env.CONTROLLER_NODES=${CONTROLLER_NODE} \
	--set manifests.each_container_is_pod=true
helm install --name contrail-analytics ${CHD_PATH}/contrail-analytics \
	--namespace=openstack --set contrail_env.CONTROLLER_NODES=${CONTROLLER_NODE} \
	--set manifests.each_container_is_pod=true
# Edit contrail-vrouter/values.yaml and make sure that images.tags.agent_vrouter_init_kernel is right.
# Image tag name will be different depending upon your linux. Also set the conf.host_os to ubuntu or centos depending on your system
helm install --name contrail-vrouter ${CHD_PATH}/contrail-vrouter \
	--namespace=openstack --set contrail_env.CONTROLLER_NODES=${CONTROLLER_NODE} \
	--set manifests.each_container_is_pod=true
# Install remaining openstack charts
cd $OSH_PATH
bash tools/deployment/developer/15-compute-kit.sh
bash tools/deployment/developer/17-cinder.sh
bash tools/deployment/developer/18-heat.sh
