from fabric.api import *
from fabric.contrib import files
from fabric.operations import *
from fabric.state import _AttributeDict
import json
import os
import sys
import tempfile

__version__ = '0.1.0'

DEFAULTS = dict(
    path='/var/chef',
    data_bags=['data_bags'],
    roles = ['roles'],
    cookbooks=['cookbooks'],
    log_level='info',
    recipes=[],
    run_list=[],
    json={},
)

SOLO_RB = """
log_level            :%(log_level)s
log_location         STDOUT
file_cache_path      "%(path)s"
data_bag_path        "%(path)s/data_bags" 
role_path            [ "%(path)s/roles" ]
cookbook_path        [ "%(path)s/cookbooks" ]
Chef::Log::Formatter.show_time = true
"""

class ChefDict(_AttributeDict):
    def add_recipe(self, recipe):
        self.run_list.append('recipe[{}]'.format(recipe))

    def add_role(self, role):
        self.run_list.append('role[{}]'.format(role))
    
    def _get_json(self):
        json = self['json'].copy()

        # Maintain compatibility with <v0.1
        if self['recipes']:
            map(self.add_recipe, self['recipes'])
        json['run_list'] = self['run_list']
        return json
    json = property(fget=_get_json)
    
chef = ChefDict(DEFAULTS)

chef.apt = True
""" Wether to run ``apt-get update`` and ``apt-get upgrade`` on provisioning """

def apt():
    if chef.apt:
        sudo('apt-get update')
        sudo('apt-get -y upgrade')
    

def omnibus():
    """
    Install Chef from Opscode's Omnibus installer
    """
    ctx = {
        'filename':'%(path)s/install-chef.sh' % chef,
        'url':'http://opscode.com/chef/install.sh',
    }
    if not files.exists(ctx['filename']):
        sudo('wget -O %(filename)s %(url)s' % ctx)
        with cd(chef.path):
            sudo('bash install-chef.sh')

def upload():
    ctx = {
        'roles'     : '%(path)s/roles' % chef,
        'data_bags' : '%(path)s/data_bags' % chef,
        'cookbooks' : '%(path)s/cookbooks' % chef,
        'node.json' : '%(path)s/node.json' % chef,
        'solo.rb'   : '%(path)s/solo.rb' % chef,
    }

    folders =  ['roles', 'data_bags', 'cookbooks']
    
    listify = lambda what: what if isinstance(what, list) else [what]
    
    chef.roles     = listify(chef.roles)
    chef.data_bags = listify(chef.data_bags)
    chef.cookbooks = listify(chef.cookbooks)

    tmpfolder = tempfile.mkdtemp()

    local('mkdir %s/roles' % tmpfolder)
    local('mkdir %s/data_bags' % tmpfolder)
    local('mkdir %s/cookbooks' % tmpfolder)

    def copyfolder(folder, what):
        if not os.path.exists(folder):
            os.makedirs(folder)

        with settings(warn_only = True):
            local('cp -r %(folder)s/* %(tmpfolder)s/%(what)s' % dict(
                    folder = folder,
                    tmpfolder = tmpfolder,
                    what = what))

    # Prepare new cookbooks, data bags etc 
    for what in folders:
        map(lambda f: copyfolder(f, what), getattr(chef, what))
        
    local('cd %s && tar -f cookbooks.tgz -cz ./cookbooks ./data_bags ./roles' % tmpfolder)

    # Get rid of old files
    with settings(warn_only = True):
        map(lambda what: sudo('rm -rf %s' % ctx[what]), folders + ['node.json', 'solo.rb'])

    # Upload
    put('%s/cookbooks.tgz' % tmpfolder, chef.path, use_sudo=True)

    with cd(chef.path):
        sudo('tar -xf cookbooks.tgz')

    files.append(ctx['node.json'], json.dumps(chef.json), use_sudo=True)
    files.append(ctx['solo.rb'], SOLO_RB % chef, use_sudo=True)

@task(default=True)
@parallel
def provision(_omnibus=True):
    sudo('mkdir -p %(path)s' % chef)

    apt()
    omnibus()
    upload()

    runchef()

@task
@parallel
def runchef():
    with cd(chef.path):
        sudo('chef-solo -c solo.rb -j node.json')
    
