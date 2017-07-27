# Releasing and deploying a new version of Libravatar

First, start by preparing a new package on the **development machine**:

    dch -i
    fab prepare

and then build it inside the **staging container**:

    make package

Finally, use the **development machine** to update the repository on `apt.libravatar.org`:

    fab update_repo

and deploy to the mirrors and master:

    fab deploy_seccdn
    fab deploy_master
