import docker
import random
from uuid import uuid4

CLIENT = docker.Client(version="1.22")


class Container:
    def __init__(self, image, tag, agent=False, ports=None):
        self.image = image
        self.tag = tag
        self.name = uuid4()
        self.ports = ports or {}
        self._inst = None
        self._logs = {}
        self._mount = agent
        self._create()

    def _create(self):
        print("Creating {} container named {}".format(self.tag, self.name))
        volumes = (
            {"/dev/log": {"bind": "/dev/log", "mode": "rw"}} if self._mount else {}
        )
        self._inst = CLIENT.create_container(
            detach=False,
            host_config=CLIENT.create_host_config(binds=volumes, port_bindings=self.ports),
            image=f"{self.image}:{self.tag}",
            ports=list(self.ports.keys()),
        )
        CLIENT.start(container=self._inst)

    def delete(self):
        print(f"Deleting {self.name}")
        CLIENT.remove_container(self._inst, v=True, force=True)

    def execute(self, command):
        exec_inst = CLIENT.exec_create(container=self._inst, cmd=command, stdout=True)
        print(f"{self.name} is executing: {command}")
        return CLIENT.exec_start(exec_id=exec_inst).decode()

    def logs(self, file="stdout", tailing=False):
        if file == "stdout":
            current = CLIENT.logs(self._inst["Id"])
        else:
            current = self.execute(f"cat {file}")
        if isinstance(current, bytes):
            current = current.decode()
        self._logs[file] = current
        return current.replace(self._logs.get(file, ""), "") if tailing else current

    def port(self):
        return CLIENT.port(self._inst["Id"], 22)[0]["HostPort"]

    def register(
        self,
        host,
        ak=None,
        org="Default_Organization",
        env="Library",
        auth=("admin", "changeme"),
        force=False,
    ):
        self._host = host
        res = self.execute(
            f"curl --insecure --output katello-ca-consumer-latest.noarch.rpm https://{host}/pub/katello-ca-consumer-latest.noarch.rpm"
        )
        res += self.execute("yum -y localinstall katello-ca-consumer-latest.noarch.rpm")
        if "Complete!" not in res:
            print("Unable to install bootstrap rpm")
            return res
        reg_command = f'subscription-manager register --org="{org}"'
        if force:
            reg_command += " --force"
        if ak:
            res += self.execute(f'{reg_command} --activationkey="{ak}"')
        else:
            res += self.execute(
                f'{reg_command} --user="{auth[0]}" --password="{auth[1]}" --environment="{env}"'
            )
        return res

    def rex_setup(self, host=None):
        self.execute("mkdir /root/.ssh")
        return self.execute(
            f"curl -ko /root/.ssh/authorized_keys https://{host or self._host}:9090/ssh/pubkey"
        )


class ContainerHost:
    def __init__(self, tag="rhel7", count=1, mount_rhsm_log=False):
        if isinstance(tag, list):
            self.container = {}
            for _tag in tag:
                self.container[_tag] = [
                    Container(_tag, mount_rhsm_log) for _ in range(count)
                ]
                if len(self.container[_tag]) == 1:
                    self.container[_tag] = self.container[_tag][0]
        else:
            self.container = [Container(tag, mount_rhsm_log) for _ in range(count)]

    def __enter__(self):
        return self.container if len(self.container) > 1 else self.container[0]

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if isinstance(self.container, dict):
            for container in self.container.values():
                container.delete()
        else:
            for container in self.container:
                container.delete()
