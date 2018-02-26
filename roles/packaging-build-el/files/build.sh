#!/bin/bash
set -exu

export kver=3.10.0-693.11.1.el7.x86_64 #new kernel version

mkdir -p /lib/modules/${kver}
test -L /lib/modules/${kver}/build || ln -s /usr/src/kernels/${kver}/ /lib/modules/${kver}/build

python $WORKDIR/contrail/third_party/fetch_packages.py

cat <<EOF > $WORKDIR/contrail/tools/packages/rpm/contrail/dkms.conf.in
PACKAGE_NAME=vrouter
PACKAGE_VERSION="__VERSION__"
PRE_BUILD="utils/dkms/gen_build_info.sh __VERSION__ \$dkms_tree/vrouter/__VERSION__/build"
MAKE[0]="'make' -C . KERNELDIR=/lib/modules/${kver}/build"
CLEAN[0]="'make' -C . KERNELDIR=/lib/modules/${kver}/build"
BUILT_MODULE_NAME[0]="vrouter"
DEST_MODULE_LOCATION[0]="/kernel/net/vrouter"
AUTOINSTALL="yes"
EOF

SCONSFLAGS="-j 8 -Q debug=1" rpmbuild \
     --define "_kVers $kver" \
     --define "_sbtop ${WORKDIR}/contrail" \
     --ba \
     tools/packages/rpm/contrail/contrail.spec

cd $WORKDIR/contrail
git clone https://github.com/Juniper/contrail-packaging tools/packaging

git clone https://github.com/Juniper/contrail-provisioning tools/provisioning

cd controller
# contrail-nodemgr.rpm
rpmbuild --define "_topdir ${WORKDIR}/contrail" --define "_builddir ${WORKDIR}/contrail/controller" -ba --define "_buildTag 12345.3" --define "_srcVer 5.0.0" ../tools/packaging/common/rpm/contrail-nodemgr.spec 

# contrail-openstack-analytics.rpm
rpmbuild --define "_topdir ${WORKDIR}/contrail" -ba --define "_buildTag 12345.3" --define "_srcVer 5.0.0" ../tools/packaging/common/rpm/contrail-openstack-analytics.spec 

# contrail-openstack-control.rpm
rpmbuild --define "_topdir ${WORKDIR}/contrail" -ba --define "_buildTag 12345.3" --define "_srcVer 5.0.0" ../tools/packaging/common/rpm/contrail-openstack-control.spec 

rpmbuild --define "_topdir ${WORKDIR}/contrail" -ba --define "_buildTag 12345.3" --define "_srcVer 5.0.0" ../tools/packaging/common/rpm/contrail-openstack-config-common.spec

rpmbuild --define "_topdir ${WORKDIR}/contrail" -ba --define "_buildTag 12345.3" --define "_srcVer 5.0.0" ../tools/packaging/common/rpm/contrail-openstack-config.spec

rpmbuild --define "_topdir ${WORKDIR}/contrail" -ba --define "_buildTag 12345.3" --define "_srcVer 5.0.0" --define "_skuTag mitaka" ../tools/packaging/common/rpm/contrail-openstack-vrouter.spec

# contrail-openstack-webui.rpm
rpmbuild --define "_topdir ${WORKDIR}/contrail" -ba --define "_buildTag 12345.3" --define "_srcVer 5.0.0" ../tools/packaging/common/rpm/contrail-openstack-webui.spec

# contrail-setup.rpm
ln -s `pwd`/tools/packaging/build/package_configs/centoslinux7{1,41708}/
ln -s `pwd`/tools/packaging/build/package_configs/ controller/build/package_configs 
rpmbuild --define "_topdir ${WORKDIR}/contrail" -ba  --define "_builddir ${WORKDIR}/contrail/controller' --define '_skuTag mitaka" --define "_buildTag 12345.3" --define "_srcVer 5.0.0" tools/packaging/common/rpm/contrail-setup.spec

# contrail-utils.rpm
rpmbuild --define "_topdir ${WORKDIR}/contrail" -ba --define "_skuTag mitaka" --define "_buildTag 12345.3" --define "_srcVer 5.0.0" tools/packaging/common/rpm/contrail-utils.spec

# contrail-vrouter-init.rpm
rpmbuild --define "_topdir ${WORKDIR}/contrail" -ba --define "_skuTag mitaka" --define "_buildTag 12345.3" --define "_srcVer 5.0.0" tools/packaging/common/rpm/contrail-vrouter-init.spec

# contrail-vrouter-dpdk.rpm - somehthing is no yes, liburcu2 is a ubuntu package name I think
#rpmbuild --define "_topdir ${WORKDIR}/contrail" -ba --define "_skuTag mitaka" --define "_buildTag 12345.3" --define "_srcVer 5.0.0" tools/packaging/common/rpm/contrail-vrouter-dpdk.spec

rpmbuild --define "_topdir ${WORKDIR}/contrail" -ba --define "_skuTag mitaka" --define "_buildTag 12345.3" --define "_srcVer 5.0.0" tools/packaging/common/rpm/contrail-vrouter-dpdk-init.spec

# neutron-plugin-contrail.rpm
rpmbuild --define "_topdir ${WORKDIR}/contrail" -ba --define "_skuTag mitaka" --define "_buildTag 12345.3" --define "_srcVer 5.0.0" tools/packaging/common/rpm/neutron-plugin-contrail.spec

# contrail-web-core.rpm
yum install -y nodejs-0.10.35-1contrail.el7
cd ${WORKDIR}/contrail/contrail-web-core
make package REPO=../contrail-web-core
cd ..
# Build binaries only, SRPMS broken
rpmbuild -bb --define "_builddir ${WORKDIR}/contrail/BUILD" --define "_buildTag 12345.3" --define "_srcVer 5.0.0" tools/packaging/common/rpm/contrail-web-core.spec

# contrail-web-controller.rpm
cd contrail-web-core # Yup, same makefile.
make package REPO=../contrail-web-controller
cd ..
# Build binaries only, SRPMS broken
rpmbuild -bb --define "_builddir ${WORKDIR}/contrail/BUILD" --define "_buildTag 12345.3" --define "_srcVer 5.0.0" tools/packaging/common/rpm/contrail-web-controller.spec
