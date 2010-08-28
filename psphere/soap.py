"""
A leaky wrapper for the underlying suds library.
"""

import sys
import urllib2
import suds
from pprint import pprint

#import logging
#logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)
#logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)

class VimFault(Exception):
    def __init__(self, fault):
        self.fault = fault
        self.fault_type = fault.__class__.__name__
        self._fault_dict = {}
        for attr in fault:
            self._fault_dict[attr[0]] = attr[1]

        Exception.__init__(self, '%s: %s' % (self.fault_type, self._fault_dict))

class VimSoap(object):
    def __init__(self, url):
        self.client = suds.client.Client('file:///home/jonathan/projects/Personal/psphere/resources/vimService.wsdl')
        #self.client = suds.client.Client(url + '/vimService.wsdl')
        self.client.set_options(location=url)

    def create(self, type):
        """Create a suds object of the requested type."""
        return self.client.factory.create('ns0:%s' % type)

    def invoke(self, method, **kwargs):
        """Invoke a method on the underlying soap service.

        >>> si_mo_ref = ManagedObjectReference('ServiceInstance',
                                               'ServiceInstance')
        >>> vs = VimSoap(url)
        >>> vs.invoke('RetrieveServiceContent', _this=si_mo_ref)

        """
        try:
            # Proxy the method to the suds service
            result = getattr(self.client.service, method)(**kwargs)
        except AttributeError, e:
            print('Unknown method: %s' % method)
            sys.exit()
        except urllib2.URLError, e:
            pprint(e)
            print('A URL related error occurred while invoking the "%s" '
                  'method on the VIM server, this can be caused by '
                  'name resolution or connection problems.' % method)
            print('The underlying error is: %s' % e.reason[1])
            sys.exit()
        except suds.client.TransportError, e:
            pprint(e)
            print('TransportError: %s' % e)
        except suds.WebFault, e:
            # Get the type of fault
            print('Fault: %s' % e.fault.faultstring)
            if len(e.fault.faultstring) > 0:
                raise

            detail = e.document.childAtPath('/Envelope/Body/Fault/detail')
            fault_type = detail.getChildren()[0].name
            fault = self.create(fault_type)
            if isinstance(e.fault.detail[0], list):
                for attr in e.fault.detail[0]:
                    setattr(fault, attr[0], attr[1])
            else:
                fault['text'] = e.fault.detail[0]

            raise VimFault(fault)

        return result

class ManagedObjectReference(suds.sudsobject.Property):
    """Custom class to replace the suds generated class, which lacks _type."""
    def __init__(self, mor=None, type=None, value=None):
        if mor:
            suds.sudsobject.Property.__init__(self, mor.value)
            self._type = str(mor._type)
        else:
            suds.sudsobject.Property.__init__(self, value)
            self._type = str(type)

