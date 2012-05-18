from fabric.api import *
from provision import chef, provision

env.hosts = ['vagrant@localhost:2222']

# Uncomment to use the Opscode Omnibus installer
# chef.use_omnibus_installer = True

chef.add_recipe('python')
chef.path = '/var/chef-solo'
