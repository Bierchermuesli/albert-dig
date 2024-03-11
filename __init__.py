# -*- coding: utf-8 -*-

"""runs DIG-like DNS Queries (and fake DIG output for your sophisticated mails / ticketing system)

Synopsis: <trigger> {domain|ip addr} [TXT|AAAA|ANY...] [@1.2.3.4.]"""

from albert import *
import os
from dns.resolver import NXDOMAIN, NoAnswer, Resolver, Timeout, NoNameservers
import dns.reversename
import ipaddress
import time
# import re

md_iid = "2.1"
md_version = "1.4"
md_id = "d"
md_name = "DNS DIG"
md_description = "dig - a dns lookup tool"
md_license = "MIT"
md_url = "https://github.com/Bierchermuesli/albert-dig"
md_maintainers = "@Bierchermuesli"
md_authors = "@Bierchermuesli"
md_lib_dependencies = ["dnspython","ipaddress"]


#default types
valid_qtype_list=["A","AAAA","NS","MX","TXT","SOA","CNAME","SRV"]
any_qtype_list=["A","AAAA","NS","MX"]
default_qtype_list=["A","AAAA"]

def is_ip(ip):
    try:
        ip = ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False
    except:
        return False


class Plugin(PluginInstance, GlobalQueryHandler):
    def __init__(self):
        GlobalQueryHandler.__init__(self, id=md_id, name=md_name, description=md_description, defaultTrigger="dig ", synopsis="{domain|ip addr} [TXT|AAAA|ANY...] [@1.2.3.4.]")
        PluginInstance.__init__(self, extensions=[self])
    
    def handleTriggerQuery(self,query):
    
        qtype=''
        qtype_list=[]
        qname=''
        response=[]

        resolver = Resolver()
        resolver.timeout = 1
        resolver.lifetime = 1


        """
        try to find any query type flag or @ask-another-resolver option?
        """
        qstring = query.string.split()
        # <triger> example.com AAAA
        if len(qstring) == 2:
            qname = qstring[0]        
            
            if qstring[1].startswith('@'):
                if is_ip(qstring[1][1:]):
                    resolver.nameservers = [qstring[1][1:]]
                    debug("we ask this resolver:"+qstring[1][1:])
            else:
                qtype = qstring[1]
        # <triger> example.com AAAA @1.2.3.4
        elif len(qstring) == 3:
            qname = qstring[0] 
            qtype = qstring[1]
            if qstring[2].startswith('@'):
                if is_ip(qstring[2][1:]):
                    resolver.nameservers = [qstring[2][1:]]
                    debug("we ask this resolver:"+qstring[2][1:])
        # <triger> example.com
        elif len(qstring):
            qname = qstring[0] 
        else:
            qname =''

        """
        try to sort qname as quick as possible and limit unnessessary queries (e.g. max 6 levels. needs a tld etc..)
        regex might be an option but probably slower...
        
        finally check if it is a ip address at and set PTR Flags/in-arpa domain

        """
        if len(qname) not in range(3, 255):
            debug("too short/Long")
            pass
        
        elif len(qname.split(".")) in range(1,6) and qname.split('.')[-1].isalpha() and len(qname.split('.')[-1]) >= 2:
            debug(qname+"-->  must be a host")
            if not qtype:
                qtype_list=default_qtype_list
            elif qtype.upper() == "ANY":
                qtype_list=any_qtype_list
            elif qtype.upper() in valid_qtype_list:
                qtype_list=[qtype.upper()]
            else:
                qtype_list=["A"]
        elif is_ip(qname):
            debug(qname+"-->  is a ip")
            qtype_list=["PTR"]
            qname = dns.reversename.from_address(qname)
        else:
            pass
            debug("nothing")



        """
        Do the query, collect output and generate fake DIG CLI outputs
        """
        digcli = []
        digclishort = []
        for qtype in qtype_list:
            error = 'NOERROR'
            start_time = time.time()
            response=[]
            debug("dig {0} {1} ".format(qname,qtype))

            digclishort.append("\n$> dig {0} {1} +short\n".format(qname,qtype))
            digcli.append("\n$> dig {0} {1}\n".format(qname,qtype))
            
            try:
                response = resolver.resolve(qname,qtype)
            except NXDOMAIN:
                debug("NXDOMAIN for {} IN {}".format(qtype,qname))
                error = "NXDOMAIN"
            except NoAnswer:
                debug("NoAnser for {} IN {}".format(qtype,qname))
                error = "NoAnswer"
            except Timeout:
                debug("timeout for {} IN {}".format(qtype,qname))
                error = "TIMEOUT"
            except dns.exception.SyntaxError:
                debug("syntax Error for {} IN {}".format(qtype,qname))
                error = "syntax Error"
            except NoNameservers as e:
                debug(f"{e}")
                error = str(e)
        
            digcli.append("; <<>> Albert-DIG {} <<>> {}\n".format(md_version,qname))
            digcli.append(";; ->>HEADER<<- opcode: QUERY, status: {}\n".format(error))
            digcli.append(";; flags: qr rd ra; QUERY: 1, ANSWER: {}, AUTHORITY: 0, ADDITIONAL: 0\n\n".format(len(response)))
            digcli.append(";; QUESTION SECTION:\n;{}.\t\tIN\t{}\n\n".format(qname,qtype))
            
            debug("{0} {1} records {2}.".format(qtype,qname,len(response)))

            digcli +=";; ANSWER SECTION:\n"
            if len(response)>0:
                for i in response:  
                    #we want cli output for all responses... - therefore a dedicated loop
                    digcli.append("{}\t\tIN\t{}\t{}\n".format(qname,qtype,i))
                    digclishort.append("{}".format(i))

                digcli.append("\n;; Query time: {} msec\n".format(round(time.time() - start_time,2)))
                digcli.append(";; SERVER: {}#53)\n".format(resolver.nameservers[0]))
                digcli.append(";; WHEN: {}\n".format(time.ctime()))

                for i in response:
                    #prepare Action list
                    actions = [
                    Action("clip","Copy {}".format(i), lambda: setClipboardText(str(i))),
                    Action("clip","Copy all dig output +short", lambda: setClipboardText(str(''.join(digclishort)))),
                    Action("clip","Copy all dig output", lambda: setClipboardText(str(''.join(digcli)))),
                    ]
                    if qtype == 'PTR':
                        actions.extend([Action("clip","Copy {}".format(qname), lambda: setClipboardText(str(qname)))])

                    #append a an item for each result             
                    query.add(StandardItem(id=md_id,
                        iconUrls = [os.path.dirname(__file__)+"/ico/"+qtype.lower()+".svg"],
                        text = str(i),  
                        subtext = "dig {0} {1} ".format(qname,qtype),
                        actions=actions
                    ))
            else:
                #output for nxdomain etc...
                digcli.append("{}\t\tIN\t{}\t\n".format(qname,qtype))
                digclishort.append("<nothing>")
                digcli.append("\n;; Query time: {} msec\n".format(round(time.time() - start_time,2)))
                digcli.append(";; SERVER: {}#53\n".format(resolver.nameservers[0]))

                digcli.append(";; WHEN: {}\n".format(time.ctime()))
                query.add(StandardItem(
                    iconUrls = [os.path.dirname(__file__)+"/ico/error.svg"],
                    text = str(error),  
                    subtext = "dig {0} {1} ".format(qname,qtype),
                    actions = [
                        Action("clip","{}".format(error), lambda: setClipboardText(str(error))),
                            Action("clip","Copy dig output +short", lambda: setClipboardText(str(''.join(digclishort)))),
                            Action("clip","Copy dig output", lambda: setClipboardText(str(''.join(digcli)))),
                        ]
                ))
