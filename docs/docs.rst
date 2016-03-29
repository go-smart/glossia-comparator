Documentation workflow
======================

This documentation is created primarily using Markdown, for simplicity,
but using Sphinx. As such, ``index.rst`` files are in reStructuredText,
as are any docstrings.

To regenerate and upload a new documentation version:

.. code-block:: sh

    cd docs/
    make apidocs
    make html
    ghp-import -n _build/html
    git push origin gh-pages

This should become visible at https://go-smart.github.io/glossia.
