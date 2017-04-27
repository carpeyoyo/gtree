# gtree
GUI interface for creating a visual graph of a git repository's commits and branches using Python 3, pygit2, PyGraphviz, and PyGTK3+. 

When gtree is run from a directory, it will check that directory for a git repository. If it finds one it will launch a window that displays a graph where each commit is represented by a node and the branches are shown as connecting edges. The edges making up the master branch are shown in green, and the edges making up the current branch are shown in blue. Clicking on a node will display the corresponding commit's information much like what is displayed in using the 'git log' command. Finally, the checklist on the left will determine which branches are displayed on the graph.

### Installation
Gtree was designed and tested on Xubuntu 17.04 using the default Python 3 version installed. The pygit2 and graphviz modules were installed using pip3. This progam was designed with the intention of being called from the command line, so an alias can be created in the user's .bashrc file: 

`alias gtree=/path_to_directory_containing_gtree/gtree.py`

that will call gtree when needed. 

### License
Gtree is licensed under the GNU General Public License v3.0, see included LICENSE file for details.