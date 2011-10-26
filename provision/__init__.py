from fabric.api import *
from fabric.contrib.files import append
from fabric.operations import *
from fabric.state import _AttributeDict
import json
import os
import sys
import tempfile

__version__ = '0.0.1'

DEFAULTS = dict(
    path='/var/chef',
    cookbooks='cookbooks',
    log_level='info',
    gems='1.8.10',
    recipes=[],
    json={},
)

SOLO_RB = """
log_level            :%(log_level)s
log_location         STDOUT
file_cache_path      "%(path)s"
cookbook_path        [ "%(path)s/cookbooks" ]
Chef::Log::Formatter.show_time = true
"""

CHEF_DEPENDENCIES = """
libopenid-ruby
liberubis-ruby
libjson-ruby
libextlib-ruby
libstomp-ruby
libohai-ruby
libopenssl-ruby
"""

class ChefDict(_AttributeDict):
    def add_recipe(self, recipe):
        self.recipes.append(recipe)
    
    def _get_json(self):
        json = self['json'].copy()
        json['recipes'] = self['recipes']
        return json
    json = property(fget=_get_json)
    
chef = ChefDict(DEFAULTS)

def apt():
    sudo('apt-get update')
    sudo('apt-get -y upgrade')
    sudo('apt-get install -y ruby ruby-dev wget %s' % ' '.join(CHEF_DEPENDENCIES.split('\n')))

def gems():
    gems = '%s/rubygems-%s.tgz' % (chef.path, chef.gems)
    gemsurl = 'http://production.cf.rubygems.org/rubygems/rubygems-%s.tgz' % (chef.gems)    
    sudo('if [ ! -f %s ]; then wget -O %s %s; fi' % (gems, gems, gemsurl))
    
    with cd(chef.path):
        sudo('tar -xf %s' % gems)
        with cd(os.path.split(os.path.splitext(gems)[0])[1]):
            sudo('ruby setup.rb install --no-format-executable --no-rdoc --no-ri')
    
    sudo('if [ ! `which chef-solo` ]; then gem install chef --no-rdoc --no-ri -n /usr/local/bin; fi')

def upload():
    sudo('mkdir -p %s' % chef.path)
    tmpfolder = tempfile.mkdtemp()
    local('mkdir %s/cookbooks && cp -r %s/* %s/cookbooks/' % (tmpfolder, os.path.normpath(chef.cookbooks), tmpfolder))
    local('cd %s && tar -f cookbooks.tgz -cz ./cookbooks' % tmpfolder)
    put('%s/cookbooks.tgz' % tmpfolder, chef.path, use_sudo=True)
    sudo('if [ -d %s/cookbooks ]; then rm -rf %s/cookbooks; fi' % (chef.path, chef.path))
    sudo('if [ -f %s/node.json ]; then rm %s/node.json; fi' % (chef.path, chef.path))
    sudo('if [ -f %s/solo.rb ]; then rm %s/solo.rb; fi' % (chef.path, chef.path))
    with cd(chef.path):
        sudo('tar -xf cookbooks.tgz')
    append('%s/node.json' % chef.path, json.dumps(chef.json), use_sudo=True)
    append('%s/solo.rb' % chef.path, SOLO_RB % chef, use_sudo=True)

@task(default=True)
def provision():
    apt()
    gems()
    upload()
    with cd(chef.path):
        sudo('chef-solo -c solo.rb -j node.json')
    
    
    
