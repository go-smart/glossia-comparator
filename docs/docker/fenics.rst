Go-Smart Simulation Architecture - FEniCS Family
================================================

This is a family within the `Docker+CGAL
workflow <overview.md#dockercgal-workflow>`__, incorporating meshing
from
`mesher-cgal <https://go-smart.github.io/gssf/tools/mesher-cgal/>`__ and
simulation provided by `FEniCS <http://fenicsproject.org/>`__. FEniCS is
a general-purpose finite element framework, capable of automated
solution of PDEs.

The
`dolfin-convert <https://github.com/FEniCS/dolfin/blob/master/scripts/dolfin-convert/dolfin-convert>`__
script is used to translate the volumetric `MSH <http://gmsh.info>`__
into DOLFIN-XML, for direct import into the Python script. The reference
upstream Docker image for this is
`fenicsproject/stable-ppa <https://bitbucket.org/fenics-project/docker>`__.

Definition
----------

The definition used for this family should be one or a series of Python
files, containing a ``start.py``. This has access to all the FEniCS
dependencies, including many core scientific Python libraries.
