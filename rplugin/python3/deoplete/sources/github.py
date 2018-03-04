from .base import Base
import netrc
import re
from urllib.parse import urlparse
import urllib.request as request
import json
import base64

def repo_homepage(vim):
    """Return the repo homepage, akin to rhubarb#repo_request
    function

    :returns: String like "https://github.com/user/repo"
    """

    repo_url = vim.eval('fugitive#repo().config("remote.origin.url")')
    homepage = vim.call('rhubarb#homepage_for_url', repo_url)
    return homepage

def repo_base(vim):
    """
    :vim: Vim Object
    :returns: API endpoint for current repo
    """
    base = repo_homepage(vim)
    if base:
        if re.search('//github\.com/', base) is not None:
            base = base.replace('//github.com/', '//api.github.com/repos/')
        else:
            # I'm not sure how to work this
            # It's enterprise github, I don't understand vim regex
            base = "failure"
            pass

    return base

def authenticator(hostname):
    """Parse netrc file into a dict

    :hostname: Hostname to get authenticator for
    :returns: Dict with login, account and password key

    """
    myrc = netrc.netrc()
    authenticator = myrc.authenticators(hostname)

    return {'login': authenticator[0],
            'account': authenticator[1],
            'password': authenticator[2]}

class Source(Base):

    """Fetches issues from Github API."""

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'github'
        self.mark = '[GH]'
        self.filetypes = ['gitcommit']
        self.input_pattern = '#'

    def gather_candidates(self, context):
        """Gather candidates from github API
        """

        base = repo_base(self.vim)

        if base:
            base = base + '/issues?per_page=200'

            base_url = urlparse(base)
            credentials = authenticator(base_url.hostname)

            r = request.Request(base)
            creds = base64.encodestring(bytes('%s:%s' % (credentials.get('login'), credentials.get('password')), 'utf-8')).strip()
            r.add_header('Authorization', 'Basic %s' % creds.decode('utf-8'))

            with request.urlopen(r) as req:
                response_json = req.read().decode('utf-8')
                response = json.loads(response_json)

                titles = [x.get('title', '') for x in response]
                numbers = [{'word': '#' + str(x.get('number', '')),
                            'menu': x.get('title'),
                            'info': x.get('body')}
                        for x in response]
                titles = [{'word': x.get('title'),
                           'menu': '#' + str(x.get('number', '')),
                           'info': x.get('body')}
                           for x in response]
                return numbers + titles
        return []
