# Bet Master

Bet Master is a peer-to-peer sports betting website using bitcoin. Bet Master was created for my final project for SE 575 (Software Design)

## Installation

1) Have Python 3 installed and referenced in your machine's path
2) Install and begin running Docker Desktop: If you don't already have it installed, visit [here](https://www.docker.com/products/docker-desktop) for download instructions
3) After cloning this repo, to install all of the Python packages required to run this application first create a virtual environment. To install the virtualenv Python package use the command:

```bash
pip3 install virtualenv
```
4) After the virtualenv package has finished installing, at the same level as the "Bet-Master-master" directory, run a command to create a virtual environment:
```bash
virtualenv myenv
```
5) After the virtual environment has been created, activate the virtual environment by running the command:
```bash
source myenv/bin/activate
```
6) Now that the virtual environment is created and running in your directory, cd into the repos first child directory (where requirements.txt is located). Now the required python packages to run this application need to be installed. To do this run the command:
```bash
pip3 install -r requirements.txt
```

## Usage

1. This application uses a uses a channel layer that uses Redis as a backing store. Start a Redis server on port 6379 using the command:

```bash
docker run -p 6379:6379 -d redis:2.8
```
2. Once the Redis server is running, begin serving the application locally on port 8000 by using the command:
```bash
python3 manage.py runserver
```

In a browser of your choice, go to the URL: **localhost:8000**

As you login, be patient, the API is very slow and there may be many games to fetch data for. 

If there are any issues that prevent you from running this application please don't hesitate to reach out to me at af885@drexel.edu or via Slack
