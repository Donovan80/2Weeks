__author__ = 'Robert Donovan'


##import newrelic.agent
##newrelic.agent.initialize('newrelic.ini')

# from flask import Flask
# application = Flask(__name__)

# from twoweeks import application as application
# import twoweeks.config as config

########
# main #
########
# if __name__ == "__main__":
#    application.run(debug=config.DEBUG)

from flask import Flask

application = Flask(__name__)


@application.route('/', methods=['GET'])
def index():
    return 'Hello world!'


def test():
    application.run(debug=True)


if __name__ == '__main__':
    test()
