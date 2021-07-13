## DIG
Dig like DNS lookups for copy & paste or check different flags/resolvers 'on-demand'

Default Trigger: `d {domain|ip addr} [TXT|AAAA|ANY...] [@1.2.3.4.]`


Have a look at this use case with on-demand query while chaning resolver or flags: 
![dig](https://user-images.githubusercontent.com/13567009/125499183-8890eb50-20b8-433e-8aac-ce9de2d66201.gif)

Defaults looks up A and AAA records. Additional param can be added for query type. e.g. MX,NS etc... or ANY (querries well known types). With `@x.x.x.x` you ask another resolver

dig -x is also supported for PTR lookups!

![image](https://user-images.githubusercontent.com/13567009/116216559-0b5c9480-a749-11eb-86d7-2d429ef7cfe4.png)

have a look for 'Alt'-Key for advanced copy&paste Option e.g. PTR Domains or dig output for sophisticated documentation porpose:

```
$> dig example.com A
; <<>> Albert-DIG 0.1.2 <<>> example.com
;; ->>HEADER<<- opcode: QUERY, status: NOERROR
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; QUESTION SECTION:
;example.com.		IN	A

;; ANSWER SECTION:
example.com		IN	A	93.184.216.34

;; Query time: 0.03 msec
;; SERVER: 1.1.1.1#53)
;; WHEN: Wed Apr 28 00:06:52 2021
```


😎



# Installation

Simple clone to Albert plugin dir and activate in Albert Python Modules
```
git clone https://github.com/Bierchermuesli/albert-dig.git ~/.local/share/albert/org.albert.extension.python/modules/dig
```


# Bugs / Feedback
PR and issues are always welcome, the code could be better I guess


# ToDO:
 * [ ] Allow FQDN as `@ns1.example.com` as quering name server argument (only IP allowed now) 


