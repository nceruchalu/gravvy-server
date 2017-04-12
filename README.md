# Gravvy

## About Gravvy
|         |                                                         |
| ------- | ------------------------------------------------------- |
| Author  | Nnoduka Eruchalu                                        |
| Date    | 04/18/2015                                              |
| Website | [http://gravvy.nnoduka.com](http://gravvy.nnoduka.com)  |

[Gravvy](http://gravvy.nnoduka.com) just simplified shared memories!


#### Available on Following Devices
* [iOS 7+](https://github.com/nceruchalu/gravvy-ios)
* Modern web browsers


## Technologies
* Python
* PostgreSQL
* Amazon Web Services
* REST
* Javascript
* HTML
* CSS
* [Bootstrap](http://getbootstrap.com)  *__[Used for responsive mobile interface]__*


## Software Description
| Module                    | Description                                      |
| ------------------------- | -------------------------------------------------|
| `settings.py`             | Django settings for project                      |
| `settings_secret.py`      | Secret Django settings for project               |
| `urls.py`                 | URL dispatcher for project                       |
| `utils.py`                | Utility functions useful to multiple Django apps |
| `wsgi.py`                 | WSGI config for project                          |
|                           |                                                  |
| **`apps/`**               | Django apps with backend logic                   |
| `apps/account/`           | User account representation and auth. app        |
| `apps/video/`             | Video mashup representation  app                 |
| `apps/rest/`              | [django rest framework](https://github.com/tomchristie/django-rest-framework) customizations |
|                           |                                                  |
| **`static/`**             | static files for project                         |
| `static/css/`             | CSS files                                        |
| `static/img`              | Static images                                    |
| `static/js/`              | Javascript files                                 |
|                           |                                                  |
| **`templates/`**          | Django templates used by apps                    |
| `templates/404.html`      | 404 page                                         |
| `templates/500.html`      | 500 page                                         |
| `templates/base.html`     | base template used by all templates              |
| `templates/rest_framework`|templates used for customizing browseable REST API|


### 3rd-party Python Modules
See requirements.txt


#### 3rd-party Javascript Modules
* [jQuery](http://jquery.com/) 
* [intl-tel-input](https://github.com/Bluefieldscom/intl-tel-input)
* [libphonenumber](https://github.com/googlei18n/libphonenumber)


### Design Decisions

#### REST API
##### General RESTful API Design Notes
Heroku has published a pretty good set of [design notes](https://github.com/interagent/http-api-design). 
This project tries to comply with these as much as possible.

##### Resource Identifiers
Publicly exposed identifiers (IDs), such as those exposed in RESTful URLs,
should not expose (or rely on) underlying technology. 

This [article here](http://toddfredrich.com/ids-in-rest-api.html) gives a better
explanation of what to use as resource identifiers.


## Virtual Env
Start a `virtualenv` virtual Python environment. This will create a sandbox
isolated from your existing Python installation so that installed packages
only exist within the sandbox:
```
virtualenv ENV
```

Activate the sandbox:
```
source ENV/bin/activate
```

Install python libraries:
```
pip install -r requirements.txt
```

## Deployment
### Database (On local machine)
#### Create User
```
$ psql -U postgres
$ create role nceruchalu_gravv superuser nocreaterole createdb login PASSWORD '<password>'
```

#### Create database
Create the database with the following command:
```
$ createdb -O nceruchalu_gravv -U nceruchalu_gravv nceruchalu_gravv
```

You can now access the database with the following command:
```
$ psql nceruchalu_gravv -U nceruchalu_gravv
```

### Django Setup: 
#### Settings files
The Django project is missing the `gravvy/settings_secret.py` file. A template 
version is included for help in setting up the sensitive information needed by 
the project.

#### Database Setup
Run the `python manage.py migrate` management command to create/update schema


### Server Setup Notes
These instructions here are what I did on my [Webfaction](https://www.webfaction.com/) server.

#### Virtual ENV notes
##### Create webfaction app with the following settings:
* Name: `gravvy`
* App category: `Django`
* App type: `mod_wsgi 4.4.11/Python 2.7` 
* The new application will be created in home directory (`~`) under `~/webapps/gravvy`.
* Delete the default project folder, `myproject`

##### Install Virtualenv
* Check if virtualenv is installed on your server:
  ```
  $ virtualenv --version
  -bash: virtualenv: command not found 
  ```

* If Virtualenv is missing, install it on Webfaction with the following:
  ```
  $ mkdir -p ~/lib/python2.7/
  $ easy_install-2.7 pip
  $ pip install virtualenv
  ```

* If you get a permission denied error try this command to install virtualenv
  inside your user folder:
  ```
  $ pip install --user virtualenv
  ```

* Verify that the installation was successful:
  ```
  $ virtualenv --version
  13.0.1
  ```

##### Create a virtual environment
* Turn application directory into a virtual Python environment:
  ```
  $ cd ~/webapps/gravvy
  $ virtualenv .
  ```

* This adds the folders and scripts for a virtual environment inside of the
  directory which webfaction created for our application.

* You can now activate the created environment:
  ```
  $ source bin/activate
  (gravvy) $ 
  ```

##### Install Django and other dependencies
* Once the initial Virtualenv setup is complete, you can install Django inside 
  it's `lib/python2.7/site-packages` directory
  ```
  (gravvy) $ pip install -r requirements.txt
  ```

* Modify `httpd.conf` paths to use the new python libraries and site-packages
  ```
  WSGIPythonPath /home/nceruchalu/webapps/gravvy:/home/nceruchalu/webapps/gravvy/gravvy:/home/nceruchalu/webapps/gravvy/lib/python2.7
  WSGIDaemonProcess gravvy processes=2 threads=12 python-path=/home/nceruchalu/webapps/gravvy:/home/nceruchalu/webapps/gravvy/gravvy:/home/nceruchalu/webapps/gravvy/lib/python2.7/site-packages:/home/nceruchalu/webapps/gravvy/lib/python2.7
  ```

###### Ref: http://michal.karzynski.pl/blog/2013/09/14/django-in-virtualenv-on-webfactions-apache-with-mod-wsgi/


#### `httpd.conf` Additions:
Add the following lines to ensure all requests to [www.gravvy.nnoduka.com](http://www.gravvy.nnoduka.com) are redirected to [gravvy.nnoduka.com](http://gravvy.nnoduka.com).

```
LoadModule alias_module      modules/mod_alias.so

RewriteEngine on
RewriteCond %{HTTP_HOST} ^www\.gravvy\.nnoduka\.com [NC]
RewriteRule ^(.*)$ http://gravvy.nnoduka.com$1 [L,R=301]
```

Since we are using Apache & mod_wsgi, add this line at the end of the conf file,
after `WSGIScriptAlias / ...`
```
WSGIPassAuthorization On
```
See [this post](http://dustindavis.me/basic-authentication-on-mod_wsgi.html) for details.


#### Crontab Additions
Access crontab with:
```
crontab -e
```

Edit it to perform following functionality:

* Setup PATH, PYTHONPATH to be used by cron's environment
* Restart apache every 30 minutes. This ensures minimal downtime (if at all)
* Backup database daily using configurations hidden in config file [some values redacted]

```
PATH=/home/nceruchalu/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:.

12,32,52 * * * * ~/webapps/gravvy/apache2/bin/start
0 2 * * * pg_dump -U nceruchalu_gravvy -Fc nceruchalu_gravvy > $HOME/db_backups/nceruchalu_gravvy/nceruchalu_gravvy-`date +\%Y\%m\%d`.sql 2>> $HOME/db_backups/cron.log
5 2 * * * pg_dump -U nceruchalu_gravvy nceruchalu_gravvy > $HOME/db_backups/nceruchalu_gravvy/nceruchalu_gravvy.sql 2>> $HOME/db_backups/cron.log
```

###### PostgreSQL credentials file
* Create a .pgpass file in `$HOME` with these contents
  ```
  hostname:port:database:username:password
  ```


#### Apple Push Notification Services Setup
Follow Apple's documentation on creating `.p12` files.
Do not password protect these files and convert them to `.pem` files by using the following command:
```
openssl pkcs12 -in aps_production.p12 -out aps_production.pem -nodes -clcerts
```

## Miscellaneous

#### To Run Development Server
```
python manage.py runserver 0:8000
```

#### Privacy & Terms
Generate here: [http://www.bennadel.com/coldfusion/privacy-policy-generator.htm](http://www.bennadel.com/coldfusion/privacy-policy-generator.htm)

#### To check resources used on server
```
ps -u nceruchalu -o rss,etime,pid,command | awk '{print $0}{sum+=$1} END {print "Total", sum/1024, "MB"}'
```

#### To check API performance
1. Generate a `curl-format.txt` file with the following contents:

   ```
   \n
               time_namelookup:  %{time_namelookup}\n
                  time_connect:  %{time_connect}\n
               time_appconnect:  %{time_appconnect}\n
              time_pretransfer:  %{time_pretransfer}\n
                 time_redirect:  %{time_redirect}\n
            time_starttransfer:  %{time_starttransfer}\n
                               ----------\n
                    time_total:  %{time_total}\n
   \n
   ```

2. Make a request and view the timings in seconds
   ```
   curl -w "@curl-format.txt" -s -H "Authorization: Token 57146d9e970c863266fcd89a7b175f66eefe4590" -H "Content-Type: application/json"  http://gravvy.nnoduka.com/api/v1/user/videos/ -o /dev/null
   ```
