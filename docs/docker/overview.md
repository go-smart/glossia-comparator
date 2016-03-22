# Go-Smart Simulation Architecture - Docker Workflows

This workflow consists of a per-[family](../families.md) Python module setting up
configuration and a solver wrapped in a Docker image. Strictly, there are
currently two Docker workflows: one entirely inside Docker and one using
[GSSF](https://go-smart.github.io/gssf/mesher) volumetric meshing prior to running a Docker instance.

## Definition

Definitions for families in this workflow should include a `start.py` file. This
will be called with Python in an environment containing the
[Python container module](container-module.md).

## Variants

### Docker-only Workflow

Any volumetric meshing must take place inside the Docker instance. This means
that the image must contain both a solver and a mesher (if meshing is required).

### Docker+CGAL Workflow

This hybrid scheme configures the [GSSF mesher](https://go-smart.github.io/gssf/mesher/) as would be the
case in [GSSF](https://go-smart.github.io/gssf/overview/), but stops after the volumetric
([CGAL](https://go-smart.github.io/gssf/tools/mesher-cgal/)) meshing step. This [MSH](http://gmsh.info) file is
provided as input to a simulation-only Docker instance. Combining these is
achieved by use of a family mixin, a module that generates only
[mesher-cgal](https://go-smart.github.io/gssf/mesher/) relevant parts of [GSSF-XML](https://go-smart.github.io/gssf/xml/),
`gssa.families.mesher_gssf.MesherGSSFMixin`.
This is included into, for instance, `gssa.families.fenics.FenicsFamily`. (In
fact, the same mix-in is used by GSSF itself for meshing configuration).

## Caveats

This workflow uses the [dockerlaunch](https://github.io/go-smart/dockerlaunch) daemon to orchestrate
containers while minimizing exposure of control. It must be installed and running on the host
for simulation containers to be launched by the Glossia container.
While containerized Glossia is not essential, the [exemplar setup](https://github.io/go-smart/glossia-server-side)
mounts the `dockerlaunch` socket to a known location in the Glossia container and ensures that the
internal user is in the `dockerlaunch` group necessary for socket access. This is in lieu of stable
user namespacing in Docker, and will be updated as this becomes standard.

### Container pruning

The `dockerlaunch` daemon only allows a Glossia server to kill containers with a known GUID, that
the current instance of `dockerlaunch` has created.

**To reduce the risk of denial-of-service attack on the simulation back-end, once `dockerlaunch` sees a certain level
of running containers (default: 30), it will refuse to create more and return a `Too many containers` error.**
Moreover, while the Glossia server should protect against this by tidying up automatically, if bugs are present, or
`dockerlaunch` is restarted, the number of redundant containers running creeps up without a critical number of
simultaneous simulations occuring. In this situation, manual intervention is required - an administrator should
check `sudo docker ps` on the host for orphaned or unnecessary containers and remove them. No restart is required -
once the number is reduced, `dockerlaunch` should be willing to start new simulation containers.
