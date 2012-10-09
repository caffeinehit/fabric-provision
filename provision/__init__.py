from fabric.api import *
from fabric.contrib import files
from fabric.operations import *
from fabric.state import _AttributeDict
import json
import os
import sys
import tempfile

__version__ = '0.0.7'

DEFAULTS = dict(
    path='/var/chef',
    cookbooks=['cookbooks'],
    log_level='info',
    gems='1.8.10',
    recipes=[],
    roles=[],
    json={},
    use_omnibus_installer = False,
)

SOLO_RB = """
log_level            :%(log_level)s
log_location         STDOUT
file_cache_path      "%(path)s"
cookbook_path        [ "%(path)s/cookbooks" ]
role_path            "%(path)s/roles"
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
    def add_role(self, role):
        self.roles.append(role)
    	
    def add_recipe(self, recipe):
        self.recipes.append(recipe)
    
    def _get_json(self):
        json = self['json'].copy()
        json['run_list'] = json.get('run_list', [])
        json['run_list'].extend(["recipe[%s]" % x for x in self['recipes']])
        json['run_list'].extend(["role[%s]" % x for x in self['roles']])
        return json
    json = property(fget=_get_json)
    
chef = ChefDict(DEFAULTS)
chef.apt = True


def apt():
    if chef.apt:
        sudo('apt-get update')
        sudo('apt-get -y upgrade')
    

def gems():
    sudo('apt-get install -y ruby ruby-dev wget %s' % ' '.join(CHEF_DEPENDENCIES.split('\n')))
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

def omnibus_install():
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
        'cookbooks': '%(path)s/cookbooks' % chef,
        'roles': '%(path)s/roles' % chef,
        'node.json': '%(path)s/node.json' % chef,
        'solo.rb': '%(path)s/solo.rb' % chef,
    }
    if not isinstance(chef.cookbooks, list):
        chef.cookbooks = [chef.cookbooks]
    tmpfolder = tempfile.mkdtemp()
    local('mkdir %s/cookbooks' % tmpfolder)
    for folder in chef.cookbooks:
        local('cp -r %s/* %s/cookbooks/' % (os.path.normpath(folder), tmpfolder))
    for path in ['cookbooks', 'roles', 'node.json', 'solo.rb']:
        if files.exists(ctx[path]):
            sudo('rm -rf %s' % ctx[path])
    put('%s/cookbooks' % tmpfolder, chef.path, use_sudo=True)
    put('roles', chef.path, use_sudo=True)
    files.append(ctx['node.json'], json.dumps(chef.json), use_sudo=True)
    files.append(ctx['solo.rb'], SOLO_RB % chef, use_sudo=True)

@task(default=True)
@parallel
def provision(omnibus=True):
    sudo('mkdir -p %(path)s' % chef)

    apt()

    if omnibus or chef.use_omnibus_installer:
        omnibus_install()
    else:
        gems()

    upload()

    with cd(chef.path):
        sudo('chef-solo -c solo.rb -j node.json')

@task(default=True)
def runchef():
    if not files.exists(chef.path):
        abort("Remote no such directory: %s "
              "(Host not yet provisioned. Run 'fab provision'" % chef.path)
    upload()
    with cd(chef.path):
        sudo('chef-solo -c solo.rb -j node.json')
