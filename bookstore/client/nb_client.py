"""Client to test bookstore endpoints from within a notebook.


TODO: (Clarify) We want to test our bookstore endpoints, but it's no fun having
to do this in an insecure fashion. Better would be to have some security in
place.

Example
-------

[{'base_url': '/',
  'hostname': 'localhost',
  'notebook_dir': '/Users/mpacer/jupyter/eg_notebooks',
  'password': False,
  'pid': 96033,
  'port': 8888,
  'secure': False,
  'token': '',
  'url': 'http://localhost:8888/'}]
"""
import os
from copy import deepcopy
from typing import NamedTuple

import requests
from IPython import get_ipython
from notebook.notebookapp import list_running_servers


class NotebookClient:
    """Client used to interact with bookstore from within a running notebook UI"""

    def __init__(self, nb_config):
        self.nb_config = nb_config
        self.nbserver_record = LiveNotebookServerRecord(**self.nb_config)
        # Right strip '/' so we can have full API endpoints without double '//'
        self.url = self.nbserver_record.url.rstrip("/")
        self.token = self.nbserver_record.token
        sessions_temp = self.get_sessions()
        self.sessions = {session['kernel']['id']: session for session in sessions_temp}

    @property
    def sessions_endpoint(self):
        api_endpoint = "/api/sessions/"
        return f"{self.url}{api_endpoint}"

    @property
    def kernels_endpoint(self):
        api_endpoint = "/api/kernels/"
        return f"{self.url}{api_endpoint}"

    @property
    def contents_endpoint(self):
        api_endpoint = "/api/contents/"
        return f"{self.url}{api_endpoint}"

    def get_sessions(self):
        target_url = f"{self.sessions_endpoint}"
        headers = {'Authorization': f'token {self.token}'}
        resp = requests.get(target_url, headers=headers)
        return resp.json()

    def get_kernels(self):
        target_url = f"{self.kernels_endpoint}"
        headers = {'Authorization': f'token {self.token}'}
        resp = requests.get(target_url, headers=headers)
        return resp.json()

    def get_contents(self, path):
        target_url = f"{self.contents_endpoint}{path}"
        headers = {'Authorization': f'token {self.token}'}
        resp = requests.get(target_url, headers=headers)
        return resp.json()


class LiveNotebookServerRecord(NamedTuple):
    """Representation of a live notebook server.

    This NamedTuple is an immutable representation of the object returned by
    ``notebook.notebookapp.list_running_servers()``.
    """

    base_url: str
    hostname: str
    notebook_dir: str
    password: bool
    pid: int
    port: int
    secure: bool
    token: str
    url: str


def extract_kernel_id(connection_file):
    """Helper to get a kernel id number from a filename"""
    return os.path.basename(connection_file).lstrip('kernel-').rstrip('.json')


class KernelInfo:
    """Representation of Kernel information for a running kernel

       Example
       -------
       kernel_id: str  # 'f92b7c8b-0858-4d10-903c-b0631540fb36',
       name: str  # 'dev',
       last_activity: str  #'2019-03-14T23:38:08.137987Z',
       execution_state: str  #'idle',
       connections: int  # 0 connections to the kernel
    """

    def __init__(self, kernel_id, name, last_activity, execution_state, connections):
        # TODO: verify that *args is not needed
        self.kernel_id = kernel_id
        self.name = name
        self.last_activity = last_activity
        self.execution_state = execution_state
        self.connections = connections


def python_compatible_session(session):
    """Helper to make a deep copy of a session"""
    deepcopy(session)


class NotebookSession:
    """Representation of an active session between a notebook and a kernel

       Example
       -------
       id: str  # '68d9c58f-c57d-4133-8b41-5ec2731b268d',
       path: str  # 'Untitled38.ipynb',
       name: str  # '',
       type: str  # 'notebook',
       kernel: KernelInfo
       notebook: dict  # {'path': 'Untitled38.ipynb', 'name': ''}
    """

    def __init__(self, path, name, session_type, kernel, notebook):
        # TODO: double check *args, **kwargs are not necessary
        self.path = path
        self.name = name
        self.type = session_type
        self.kernel = KernelInfo(**kernel)
        self.notebook = notebook


class NotebookClientCollection:
    """Representation of a collection of notebook clients"""

    # TODO: refactor from lambda to a def
    nb_client_gen = lambda: (NotebookClient(x) for x in list_running_servers())
    sessions = {x.url: x.sessions for x in nb_client_gen()}

    @classmethod
    def current_server(cls):
        """class method for current notebook server"""
        for server_url, session_dict in cls.sessions.items():
            for session_id, session in session_dict.items():
                python_compatible_session(session)
                if NotebookSession(**session).kernel.id == extract_kernel_id(
                    get_ipython().parent.parent.connection_file
                ):
                    return next(
                        client
                        for client in cls.nb_client_gen()
                        if client.url == server_url
                    )


class CurrentNotebookClient(NotebookClient):
    """Represents the currently active notebook client"""

    def __init__(self):
        self.nb_client = NotebookClientCollection.current_server()
        super().__init__(self.nb_client.nb_config)
        self.session = self.sessions[self.id]
        self.notebook = NotebookSession(**self.session).notebook

    @property
    def connection_file(self):
        return get_ipython().parent.parent.connection_file

    @property
    def kernel_id(self):
        return os.path.basename(self.connection_file).lstrip('kernel-').rstrip('.json')
