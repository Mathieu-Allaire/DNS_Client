# DNS Client

This DNS client is implemented in Python using socket programming. It allows to query DNS servers for `A`, `NS`, and `MX` record types. The code was developed with **Python 3.9.12**.

## Usage

To run the DNS client, use the following command:

```
python dnsClient.py [-t timeout] [-r max-retries] [-p port] [-mx | -ns] @server name
```
where the arguments are defined as follows:

- **timeout** (optional): Specifies how long to wait, in seconds, before retransmitting an unanswered query.  
  **Default value**: 5.

- **max-retries** (optional): The maximum number of times to retransmit an unanswered query before giving up.  
  **Default value**: 3.

- **port** (optional): The UDP port number of the DNS server.  
  **Default value**: 53.

- **-mx or -ns flags** (optional): Indicates whether to send a MX (mail server) or NS (name server) query.  
  At most one of these can be given, and if neither is given, the client sends a type A (IP address) query.

- **server** (required): The IPv4 address of the DNS server, in a.b.c.d. format.

- **name** (required): The domain name to query for.
