from fabric.api import *
from provision import chef, provision

env.hosts = ['vagrant@localhost:2222']

chef.add_recipe('python')
chef.path = '/var/chef-solo'
