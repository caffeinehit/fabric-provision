from fabric.api import *
from fabric.contrib import files
from fabric.operations import *
from fabric.state import _AttributeDict
import json
import os
import sys
import tempfile

__version__ = '0.0.4'

DEFAULTS = dict(
    path='/var/chef',
    cookbooks=['cookbooks'],
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
    ctx = {
        'filename':'%(path)s/rubygems-%(gems)s.tgz' % chef,
        'url':'http://production.cf.rubygems.org/rubygems/rubygems-%(gems)s.tgz' % chef,
    }    
    if not files.exists(ctx['filename']):
        sudo('wget -O %(filename)s %(url)s' % ctx)
    
    with cd(chef.path):
        sudo('tar -xf %(filename)s' % ctx)
        with cd(os.path.split(os.path.splitext(ctx['filename'])[0])[1]):
            sudo('ruby setup.rb install --no-format-executable --no-rdoc --no-ri')
        
    if not files.exists('/usr/local/bin/chef-solo'):
        sudo('gem install chef --no-rdoc --no-ri -n /usr/local/bin')

def upload():
    ctx = {
        'cookbooks': '%(path)s/cookbooks' % chef,
        'node.json': '%(path)s/node.json' % chef,
        'solo.rb': '%(path)s/solo.rb' % chef,
    }
    
    tmpfolder = tempfile.mkdtemp()
    
    local('mkdir %s/cookbooks' % tmpfolder)

    if not isinstance(chef.cookbooks, list):
        chef.cookbooks = [chef.cookbooks]
    
    for folder in chef.cookbooks:
        local('cp -r %s/* %s/cookbooks/' % (os.path.normpath(folder), tmpfolder))
        
    local('cd %s && tar -f cookbooks.tgz -cz ./cookbooks' % tmpfolder)
    
    put('%s/cookbooks.tgz' % tmpfolder, chef.path, use_sudo=True)
    
    if files.exists(ctx['cookbooks']):
        sudo('rm -rf %(cookbooks)s' % ctx)
    
    if files.exists(ctx['node.json']):
        sudo('rm -rf %(node.json)s' % ctx)
    
    if files.exists(ctx['solo.rb']):
        sudo('rm -rf %(solo.rb)s' % ctx)
    
    with cd(chef.path):
        sudo('tar -xf cookbooks.tgz')

    files.append(ctx['node.json'], json.dumps(chef.json), use_sudo=True)
    files.append(ctx['solo.rb'], SOLO_RB % chef, use_sudo=True)

@task(default=True)
def provision():
    sudo('mkdir -p %(path)s' % chef)
    apt()
    gems()
    upload()
    with cd(chef.path):
        sudo('chef-solo -c solo.rb -j node.json')
    
    
    
