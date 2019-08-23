# AUDiaL installation

This document outlines the steps to install AUDiaL on a Web server running Apache under Ubuntu.

## System Requirements

- Python 2.7 (and pip)
- Java JDK 1.8+ (optional, only if you want to run NLP locally)

## Install (Apache on Ubuntu)

1. Install Java 8 (optional):
    1. Install the JDK (1.8+):

        ```shell
        > sudo apt install openjdk-8-jdk
        ```

    2. Set the JAVA_HOME environment:

        ```shell
        > sudo nano /etc/environment
        ```

        1.  Add the following line to the environment file: `JAVA_HOME="/path/to/jdk/bin/"`
        2.  Reload the file and test it worked:

            ```shell
            > source /etc/environment
            > echo $JAVA_HOME
            ```

2. Install required header files and restart Apache:

    ```shell
    > sudo apt-get install apache2-dev
    > sudo apt-get install python-dev
    > /etc/init.d/apache2 restart
    ``` 

3. Copy AUDiaL's source code (i.e. the contents of the `/src/audial` directory) somewhere in your server e.g. `/home/audial/audial-app`.
4. If you want to install the Stanford Parser and Tagger locally: 
    1. Download the [basic English Stanford Tagger](https://nlp.stanford.edu/software/tagger.shtml#Download) (version 3.9.1).
    2. Unzip the contents of the previous file such that `stanford-postagger-X.X.X.jar` is under `/home/audial/audial-app/NLP/lib/postaggers/stanford-postagger`.
    3. Download the [Stanford Parser](https://nlp.stanford.edu/software/lex-parser.shtml#Download) (version 3.9.1).
    4. Unzip the contents of the previous file such that `stanford-parser-X.X.X-models.jar` is under `/home/audial/audial-app/NLP/lib/parsers/stanford-parser-full`.
5. Set up a Python 2.7 virtual environment (venv) in the previous directory and install the required Python modules:

    ```shell
    > pip install virtualenv
    > cd /home/audial
    > virtualenv -p python2 ./venv
    > source ./venv/bin/activate
    > (venv) pip install -r audial-app/install/requirements.txt
    ```

6. Optionally, you may also install the following modules for data analysis tasks:

    ```shell
    > (venv) pip install scipy
    > (venv) pip install scikit-learn
    ```

7. Install `mod_wsgi` into your venv. Exit venv afterwards:

    ```shell
    > (venv) pip install mod_wsgi
    > (venv) sudo ./venv/bin/mod_wsgi-express install-module
    > (venv) deactivate
    ```
   
8. If the previous step did not work, you may try installing `libapache2-mod-wsgi` globally as well:

    ```shell
    > sudo apt-get install libapache2-mod-wsgi
    ```

9.  Create a new file `/home/audial/audial.wsgi` with the following contents:

    ```python
    #!/usr/bin/python
    import os, sys
    
    PROJECT_DIR = '/home/audial'
    sys.path.insert(0, PROJECT_DIR)
    sys.path.append('/home/audial/audial-app')
    
    activate_this = os.path.join(PROJECT_DIR, 'venv/bin', 'activate_this.py' )
    execfile(activate_this, dict(__file__=activate_this))
    
    from audial import app as application
    application.debug = True
    ```

10. Your project structure should now look something like this (the `lib` subdirectory being optional):

    ```
    -/home/audial/
        |- audial-app
        |       |- NLP
        |       |   |- lib
        |       |   |    |- parsers
        |       |   |    |      |-stanford-parser-full            
        |       |   |    |- postaggers
        |       |   |           |- stanford-postagger
        |       |   |- model
        |       |   |    |...
        |       |   |...
        |       |     
        |       |- consolidator
        |       |     |...
        |       |- dialog
        |       |     |...
        |       |- logger
        |       |     |...
        |       |
        |      ...
        |       |
        |       |- __init__.py
        |- venv
        |   |- bin
        |   |   |...
        |   |- include
        |   |   |...
        |   |- lib
        |   |   |...
        |   |- share
        |       |...
        |- audial.wsgi
    ```

11. Create a new user and group e.g. flaskuser:flaskgroup and make it own the project:

    ```shell
    > chown -R flaskuser:flaskgroup /home/audial
    ```

12. Create a new Apache configuration file:

    ```shell
    > cd /etc/apache2/sites-available
    > > audial.conf
    ```

13. Configure your Virtual Host by editing `audial.conf`, for example:

    ```
    <VirtualHost *:80>
    
    ServerName audial.example.com
    ErrorLog /var/log/apache2/audial-error.log
    CustomLog /var/log/apache2/audial-access.log combined

    WSGIDaemonProcess audial user=flaskuser group=flaskgroup threads=5
    WSGIScriptAlias / /home/audial/audial.wsgi
	
	<Directory /home/audial>
        WSGIProcessGroup audial
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
		Options Indexes FollowSymLinks MultiViews
        AllowOverride All
    </Directory>
	
	<Directory /home/audial/audial-app>
        WSGIProcessGroup audial
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
		Options Indexes FollowSymLinks MultiViews
        AllowOverride All
    </Directory>

    </VirtualHost>
    ```

14. Enable the Apache Virtual Host you have just created:

    ```shell
    > sudo a2ensite audial.conf
    ```

15. Restart Apache

    ```shell
    > /etc/init.d/apache2 restart
    ``` 
    
16. Done! AUDiaL should be reachable from the Internet at audial.example.com (given a DNS entry for the subdomain exists)
