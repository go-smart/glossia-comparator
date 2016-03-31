License
=======

Individual licenses are clarified in their respective source files or, if not in a given file, it
should be inferred that the given repository's license applies. In general, Glossia tools are
released under the `GNU Affero General Public License v3 <http://www.gnu.org/licenses/agpl-3.0.en.html>`_
(GNU AGPLv3). A notable exception is
the Glossia Python Container Module, which is licensed under more relaxed terms to ease
containerization of proprietary numerics codes (however, other code in exemplar containers, such
as the Goosefoot meshing or simulation tools, may be covered by their own stricter licenses).

Where pre-existing licenses are
incompatible, specific files are *explicitly* labelled under alternate licenses. Copies of specific
licenses should be included with the source code - please contact us if it is not.

If you believe
source code is included that is incompatible with the GNU AGPLv3, please contact the Go-Smart
Consortium and, if specific issues remain, please contact us through the individual Github
repository. We have a policy of allowing re-licensing relevant source to more relaxed licenses (e.g. GPLv2/3)
specifically to enable upstream inclusion of improvements in projects we derive from.
While we are working on preparing upstream
submissions for some of our reusable code, if you see Go-Smart AGPLv3 code directly derived from your
upstream project, but require GPLv2/3 licensing to incorporate our modifications, please contact us.

Please note that the GNU AGPLv3 licence generally requires source code to be made available if a service
is provided to a third-party over a network. This affects any code modifications you choose to make
to the Glossia server, but does not
affect code that operates "`at arms length <http://www.gnu.org/licenses/gpl-faq.html#GPLInProprietarySystem>`_"
- code within a simulation container is considered to
do so, allowing AGPLv3-incompatible code to be contained within a container.
Similarly, Glossia clients
communicating over WAMP are not affected by Glossia's AGPLv3 terms.
Note, however, that
Python glue modules (families) operating within the Glossia server *are* subject to the AGPLv3 requirements.

Numerical Model configuration and code contained within GSSA-XML, passed directly from the client to the
simulation container (via Glossia), is not normally affected by licensing of Glossia. Within the default
set-up of the ``gosmart/glossia-goosefoot``, SIF templates and MATC algorithms passed to Glossia in GSSA-XML
are not affected by AGPLv3 licensing of Goosefoot.
