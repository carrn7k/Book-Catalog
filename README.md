# Book Catalog -- version 1.0

A multi-page app using Python's Flask framework. The app allows
users to write, read and update their favorite books to a DB. 

## Running the App--
	
### Dependencies - 
* Vagrant
* VirtualBox
* Python
* Flask
* Jinja2
* SQLalchemy
* jQuery
* Font-Awesome

If you don't have have Python on your machine, you'll 
need to install Python and the necessary python libraries.

Download and Install Python: https://www.python.org/downloads/

A virtual machine is needed to run the app locally. If
you don't have vagrant and VirtualBox installed on your
machine, please install them and set up your virtual
machine using the .vagrant file in the directory.

For help installing vagrant, visit the following
link: https://www.vagrantup.com/docs/getting-started/project_setup.html

This app is set to run on localhost:5000, if you wish
to change this, please reconfigure the vagrant file to 
include the port you wish to operate from. 

```ruby
  config.vm.network "forwarded_port", guest: 8000, host: 8000
  config.vm.network "forwarded_port", guest: 8080, host: 8080
  config.vm.network "forwarded_port", guest: 5000, host: 5000
```
**If you make changes to the .vagrant file, run *vagrant reload* for changes to take effect**
**You also must reconfigure the portion of application.py file shown below.**

```python
if __name__ == '__main__':
    app.debug = True
    app.secret_key = "super_secret_key"
    app.run(host='0.0.0.0', port=5000)
```
	
After all required software has been installed, open a 
terminal and navigate to the project directory /catalog.
In your terminal, type the following commands:

* vagrant up
* vagrant ssh

You should now be logged into the virtual machince. Navigate
to /vagrant/catalog to access the application files and then
type python application.py to run the app. After typing this 
command, your machine should be hostingthe app on localhost:5000
(or whatever port you've set up). Open your favorite browser 
and navigate to your local port to view the app. 
 
	
