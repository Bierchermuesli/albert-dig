# -*- coding: utf-8 -*- 

"""runs DIG-like DNS Queries (and fake DIG output for your sophisticated mails / ticketing system)

Synopsis: <trigger> {domain|ip addr} [TXT|AAAA|ANY...] [@1.2.3.4.]"""

from albert import *
from pathlib import Path
from dns.resolver import NXDOMAIN, NoAnswer, Resolver, Timeout, NoNameservers
import dns.reversename
import ipaddress
import time

md_iid = "5.0"
md_version = "2.1"
md_name = "DNS DIG"
md_description = "dig - a dns lookup tool"
md_license = "MIT"
md_url = "https://github.com/Bierchermuesli/albert-dig"
md_maintainers = ["@Bierchermuesli"]
md_authors = ["@Bierchermuesli"]
md_lib_dependencies = ["dnspython"]

# default types
VALID_QTYPES = ["A", "AAAA", "NS", "MX", "TXT", "SOA", "CNAME", "SRV", "HTTPS"]

def is_ip(address: str) -> bool:
    """Checks if a string is a valid IP address."""
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError:
        return False

class Plugin(PluginInstance, GeneratorQueryHandler):
    # --- private attributes
    _resolver_timeout = 1.0
    _resolver_lifetime = 1.0
    _default_qtypes = "A,AAAA"
    _any_qtypes = "A,AAAA,NS,MX"

    def __init__(self):
        GeneratorQueryHandler.__init__(self)
        PluginInstance.__init__(self)
        self.icon_path = Path(__file__).parent / "ico"
        self._init_configuration()

    # --- properties for settings
    @property
    def resolver_timeout(self):
        return self._resolver_timeout

    @resolver_timeout.setter
    def resolver_timeout(self, value):
        self._resolver_timeout = value
        self.writeConfig("resolver_timeout", value)

    @property
    def resolver_lifetime(self):
        return self._resolver_lifetime

    @resolver_lifetime.setter
    def resolver_lifetime(self, value):
        self._resolver_lifetime = value
        self.writeConfig("resolver_lifetime", value)

    @property
    def default_qtypes(self):
        return self._default_qtypes

    @default_qtypes.setter
    def default_qtypes(self, value):
        self._default_qtypes = value
        self.writeConfig("default_qtypes", value)
    
    @property
    def any_qtypes(self):
        return self._any_qtypes

    @any_qtypes.setter
    def any_qtypes(self, value):
        self._any_qtypes = value
        self.writeConfig("any_qtypes", value)

    def _init_configuration(self):
        """Load settings from config file or set defaults."""
        for key, type, default in [
            ("resolver_timeout", float, self._resolver_timeout),
            ("resolver_lifetime", float, self._resolver_lifetime),
            ("default_qtypes", str, self._default_qtypes),
            ("any_qtypes", str, self._any_qtypes),
        ]:
            conf = self.readConfig(key, type)
            if conf is None:
                self.writeConfig(key, default)
            else:
                setattr(self, f"_{key}", conf)

    def configWidget(self):
        return [
            {
                "type": "label",
                "text": "This plugin provides a simple DIG-like DNS query interface."
            },
            {
                "type": "doublespinbox",
                "label": "Resolver Timeout (seconds)",
                "property": "resolver_timeout",
                "widget_properties": {"minimum": 0.1, "maximum": 5.0, "singleStep": 0.1}
            },
            {
                "type": "doublespinbox",
                "label": "Resolver Lifetime (seconds)",
                "property": "resolver_lifetime",
                "widget_properties": {"minimum": 0.1, "maximum": 10.0, "singleStep": 0.1}
            },
            {
                "type": "lineedit",
                "label": "Default Query Types",
                "property": "default_qtypes",
                "widget_properties": {"placeholderText": "e.g., A,AAAA"}
            },
            {
                "type": "label",
                "text": "Comma-separated list of DNS record types to query when none is specified."
            },
            {
                "type": "lineedit",
                "label": "Query Types for 'ANY'",
                "property": "any_qtypes",
                "widget_properties": {"placeholderText": "e.g., A,AAAA,NS,MX"}
            },
            {
                "type": "label",
                "text": "Comma-separated list of DNS record types to query when 'ANY' is specified."
            }
        ]
    
    def defaultTrigger(self):
        return "dig "

    def synopsis(self, query):
        return "{domain|ip addr} [TXT|AAAA|ANY...] [@1.2.3.4.]"

    def _parse_query(self, query_string: str):
        """Parses the raw query string into qname, qtype, and resolver."""
        qname = ''
        qtype_arg = ''
        resolver_addr = None

        parts = query_string.split()
        if not parts:
            return None, None, None

        qname = parts[0]
        
        for part in parts[1:]:
            if part.startswith('@'):
                addr = part[1:]
                if is_ip(addr):
                    resolver_addr = addr
            else:
                qtype_arg = part.upper()
        
        return qname, qtype_arg, resolver_addr

    def _build_qtype_list(self, qname: str, qtype_arg: str):
        """Determines the list of query types based on the arguments."""
        if not qname:
            return []

        if is_ip(qname):
            return ["PTR"]

        if len(qname.split(".")) in range(1, 6) and qname.split('.')[-1].isalpha() and len(qname.split('.')[-1]) >= 2:
            if not qtype_arg:
                return [qt.strip() for qt in self.default_qtypes.split(',') if qt.strip()]
            if qtype_arg == "ANY":
                return [qt.strip() for qt in self.any_qtypes.split(',') if qt.strip()]
            if qtype_arg in VALID_QTYPES:
                return [qtype_arg]
        
        return [] # Return empty list for invalid qname patterns

    def _run_query(self, qname: str, qtype: str, resolver: Resolver):
        """Runs a single DNS query and returns the results and cli output."""
        start_time = time.time()
        error = 'NOERROR'
        answers = []
        
        try:
            answers = resolver.resolve(qname, qtype)
        except NXDOMAIN:
            error = "NXDOMAIN"
        except NoAnswer:
            error = "NoAnswer"
        except Timeout:
            error = "TIMEOUT"
        except dns.exception.SyntaxError:
            error = "Syntax Error"
        except NoNameservers as e:
            error = str(e)
            
        query_time = round((time.time() - start_time) * 1000)
        server = resolver.nameservers[0] if resolver.nameservers else "N/A"
        
        dig_header = [
            f"; <<>> Albert-DIG {md_version} <<>> {qname}",
            f";; ->>HEADER<<- opcode: QUERY, status: {error}",
            f";; flags: qr rd ra; QUERY: 1, ANSWER: {len(answers)}, AUTHORITY: 0, ADDITIONAL: 0\n",
            f";; QUESTION SECTION:\n;{qname}.\t\tIN\t{qtype}\n"
        ]
        
        dig_short = [f"\n$> dig {qname} {qtype} +short\n"]
        dig_full = [f"\n$> dig {qname} {qtype}\n"] + dig_header
        dig_full.append(";; ANSWER SECTION:")

        if answers:
            for answer in answers:
                dig_full.append(f"{qname}.\t\tIN\t{qtype}\t{answer}")
                dig_short.append(str(answer))
        else:
            dig_full.append(f";{qname}.\t\tIN\t{qtype}")
            dig_short.append("<nothing>")

        dig_footer = [
            f"\n;; Query time: {query_time} msec",
            f";; SERVER: {server}#53",
            f";; WHEN: {time.ctime()}"
        ]
        dig_full.extend(dig_footer)

        return answers, error, "".join(dig_full), "".join(dig_short)

    def items(self, ctx):
        qname, qtype_arg, resolver_addr = self._parse_query(ctx.query)

        if not qname:
            return

        qtype_list = self._build_qtype_list(qname, qtype_arg)
        if not qtype_list:
            # Handle cases where build_qtype_list returns empty (invalid domain)
            if not is_ip(qname): # Avoid showing this for IPs that are being reversed
                 yield [StandardItem(
                    id=md_name,
                    icon_factory=lambda: Icon.image(self.icon_path / "error.svg"),
                    text="Invalid query",
                    subtext=f"'{qname}' is not a valid domain or IP address."
                )]
            return

        resolver = Resolver()
        resolver.timeout = self.resolver_timeout
        resolver.lifetime = self.resolver_lifetime
        if resolver_addr:
            resolver.nameservers = [resolver_addr]

        # Handle reverse DNS
        if "PTR" in qtype_list:
            qname = dns.reversename.from_address(qname)

        items = []
        for qtype in qtype_list:
            answers, error, dig_full, dig_short = self._run_query(qname, qtype, resolver)
            
            actions = [
                Action("clip-short", "Copy dig output (+short)", lambda short=dig_short: setClipboardText(short)),
                Action("clip-full", "Copy full dig output", lambda full=dig_full: setClipboardText(full)),
            ]
            
            if answers:
                for answer in answers:
                    item_actions = [Action("clip-answer", f"Copy {answer}", lambda ans=answer: setClipboardText(str(ans)))] + actions
                    if qtype == 'PTR':
                         item_actions.insert(1, Action("clip-qname", f"Copy {qname}", lambda qn=qname: setClipboardText(str(qn))))
                    
                    icon_file = self.icon_path / f"{qtype.lower()}.svg"
                    if not icon_file.exists():
                        icon_file = self.icon_path / "a.svg" # Fallback icon

                    items.append(StandardItem(
                        id=md_name,
                        text=str(answer),
                        subtext=f"dig {qname} {qtype}",
                        icon_factory=lambda file=icon_file: Icon.image(file),
                        actions=item_actions
                    ))
            else:
                items.append(StandardItem(
                    id=md_name,
                    text=error,
                    subtext=f"dig {qname} {qtype}",
                    icon_factory=lambda: Icon.image(self.icon_path / "error.svg"),
                    actions=actions
                ))
        yield items