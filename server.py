import datetime
import json

import cherrypy
from dateutil.relativedelta import relativedelta
from wit import Wit


class HelloWorld(object):
    # base variables
    base_url = 'https://www.linkedin.com/talent/reports/pipeline-report'

    base_json_string = """{ 
            "owners":[]
        }"""

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self, query):
        client = Wit(access_token='3JS6UBXSRTOE6U4VF57667PKDZZ3IHOF')
        response = client.message(query)
        entities = response['entities']
        # wit returns a list of possibilities, the most probable results will always be on top
        cherrypy.log(str(entities))
        ret = json.loads(self.base_json_string)
        if 'datetime' in entities:
            date = entities['datetime'][0]
            dates = self.process_date(date)
            [start_time, end_time] = dates.split("#")
            ret['start_time'] = start_time
            ret['end_time'] = end_time
        if 'contact' in entities:
            contact = entities.get('contact', [])
            owners = self.process_owners(contact)
            ret['owners'] = owners
        if 'intent' in entities:
            intent = self.process_intent(entities['intent'][0])
            ret['intent'] = intent
        if 'job_function' in entities:
            ret['job_function']= self.process_job_function(entities['job_function'])
        return ret

    def process_date(self, input_date):
        # Useful: this is ISO-8601 std datetime string.
        format = '%Y-%m-%dT%H:%M:%S.%f%z'
        current_time = datetime.datetime.now()
        if not input_date:
            return ''
        confidence = input_date['confidence']
        cherrypy.log(str(confidence))
        if confidence < 0.5:
            cherrypy.log('The confidence level is too low, continuing')
        if 'from' in input_date and 'to' in input_date:
            start_time = datetime.datetime.strptime(input_date['from']['value'], format)
            end_time = datetime.datetime.strptime(input_date['to']['value'], format)
        else:
            start_time = datetime.datetime.strptime(input_date['value'], format)
            grain = input_date.get('grain', 'month')
            cherrypy.log(str(start_time))
            cherrypy.log(grain)
            # add grain as the end date
            end_time = datetime.datetime.now()
            if grain == 'year':
                end_time = start_time + relativedelta(years=1)
            elif grain == 'month':
                end_time = start_time + relativedelta(months=1)
            elif grain == 'week':
                end_time = start_time + relativedelta(weeks=1)
            elif grain == 'day':
                end_time = start_time = relativedelta(days=1)
        if start_time.time() < current_time.time() and end_time.time() < current_time.time():
            return str(start_time) + "#" + str(end_time)
        else:
            return ''

    def process_intent(self, input_intent):

        return input_intent['value']

    def process_owners(self, input_contact):
        output_owners = []
        # return all people where the confidence level is greater than this epsilon value
        epsilon = 0.8
        for contact in input_contact:
            confidence = contact.get('confidence', 0.0)
            if confidence > epsilon:
                cand = contact['value']
                if cand in ['my', 'me', 'I', 'your', 'yours']:
                    cand = 'urn:li:ts_seat:0'
                elif cand == 'Steve Weiss':
                    cand = 'urn:li:ts_seat:136219271'
                elif cand == 'Dan Reid':
                    cand = 'urn:li:ts_seat:0'
                output_owners.append(cand)
        return output_owners

    def process_job_function(self, input_functions):
        return input_functions[0]['value']

cherrypy.config.update({'server.socket_host': 'yefwang-mn3.linkedin.biz',
                        'server.socket_port': 11180,
                        })
cherrypy.quickstart(HelloWorld())
AQ