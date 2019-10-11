# content-host-helpers
This is a temporary repository to allow our team to experiment with creating container-based content hosts in automation.


# Container Context Manager

The container-context-manager.py file contains ContainerContext, a context manager for creating Linux containers.

## Prerequisites

* A container runtime process (Podman) or daemon (Docker) to run containers.

* A container image

## Installing

Fork the repo and clone your fork (recommended), or just clone the repo from https://github.com/JacobCallahan/content-host-helpers

## Using the Context Manager

Start your container process or daemon

You can use ipython in interactive mode to test and develop a script to use the context manager.

You can test your container environment by making one container host using the Container class:

~~~
~]# cd content-host-helpers
~]# ipython -i container-context-manager.py
In [1]: myhost = Container()
Creating rhel7 container named 365404ff-a1e5-42b7-9624-8d32c8578297
~~~

In another terminal, list the running containers:

~~~
~]$  docker ps
CONTAINER ID    IMAGE     COMMAND      CREATED     STATUS     PORTS     NAMES
19599452db1d   ch-d:rhel7  "tail -f…"       
~~~


Delete the container:

~~~
In [2]: Container.delete(myhost)                                                                                                                                             
Deleting 365404ff-a1e5-42b7-9624-8d32c8578297
~~~


Use the context manager to start two containers:

~~~
In [3]: with ContainerContext(count=2, agent=True) as chosts:
   ...:     for c_host in chosts: 
   ...:             print(c_host.execute("hostname")) 
   ...:             c_host.register("dell-r330-12.gsslab.brq.redhat.com","test_ak")
   ...:             c_host.execute("subscription-manager attach --auto")
   ...:             wait = input("Press enter to quit")
   ...:                                                                                                                                                                     
Creating rhel7 container named dfb94835-6c64-4218-beb3-24e76b786e3c
Creating rhel7 container named 8df117b8-f02e-4f6c-803d-df190d40cbb0
dfb94835-6c64-4218-beb3-24e76b786e3c is executing: hostname
ea794a67171d
~~~

Search for the host as Content Host in your Satellite, in this example named _ea794a67171d_. Confirm that registration was successful.

When this test is successful you can remove the wait statement and add further options.