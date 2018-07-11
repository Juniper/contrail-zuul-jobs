=====
About
=====

Role implemented according to the guide available at https://github.com/Juniper/contrail-kubernetes-docs.
OpenShift 3.9 installation requires a 3 node setup for RHEL.
The nodes need to be named openshift-master, openshift-infra and openshift-compute for now.
Improvements can be made using the update-ansible-inventory role and iterating
through host groups.
See the host groups definitions in ose-install.j2 inventory template.
