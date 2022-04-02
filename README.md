# v6mig_autoconfig JET App

This program is a sample implementation of [IPv6マイグレーション技術の国内標準プロビジョニング方式 【第1.1版】](https://github.com/v6pc/v6mig-prov/blob/1.1/spec.md) in Junos router by Junos Extension Toolkit(JET).

## Usage

 - Configure `set system extensions providers kazubu license-type customer deployment-scope commercial` in the device to load JET package.
 - Transfer `v6mig_autoconfig-....tgz` to /var/tmp of device.
 - Run `request system software add /var/tmp/v6mig_autoconfig-...tgz`

### Static address configuration for NGN facing interface
 - Load following configuration to Junos box(need to change NTT_EAST, ge-0/0/0 and USERNAME to appropriate value).

```
set system extensions extension-service application file ipoe_autoconfig.py arguments "--external-interface ge-0/0/0.0 --area NTT_EAST --insecure true"
set system extensions extension-service application file ipoe_autoconfig.py daemonize
set system extensions extension-service application file ipoe_autoconfig.py respawn-on-normal-exit
set system extensions extension-service application file ipoe_autoconfig.py username USERNAME
```

 - Other required configuration(need to change interface name and addresses to appropriate value):
```
set interfaces ge-0/0/0.0 unit 0 family inet6 address 2001:db8::2/64
set routing-options rib inet6.0 static route ::/0 next-hop 2001:db8::1
set routing-options static route 0/0 next-hop ip-0/0/0.0
```

### Dynamic address configuration using RA for NGN facing interface
 - Load following configuration to Junos box(need to change ge-0/0/0.0 and USERNAME to appropriate value).

```
set system extensions extension-service application file ipoe_autoconfig.py arguments "--external-interface ge-0/0/0.0 --dns-from-dhcpv6 true --insecure true"
set system extensions extension-service application file ipoe_autoconfig.py daemonize
set system extensions extension-service application file ipoe_autoconfig.py respawn-on-normal-exit
set system extensions extension-service application file ipoe_autoconfig.py username USERNAME
```

- Other required configuration(need to change interface name to appropriate value):
```
set interfaces ge-0/0/0 unit 0 family inet6 dhcpv6-client client-type autoconfig
set interfaces ge-0/0/0 unit 0 family inet6 dhcpv6-client client-ia-type ia-na
set interfaces ge-0/0/0 unit 0 family inet6 dhcpv6-client client-identifier duid-type duid-ll
set protocols router-advertisement interface ge-0/0/0.0 default-lifetime 0
set routing-options static route 0/0 next-hop ip-0/0/0.0
```


## How to build

 * TBD

## Options
 - --external-interface [Interface Name(IFL)]: Required. Specify external interface for DS-Lite tunnel.
 - --dns-from-dhcpv6 [true]: Use DNS servers received from DHCPv6. Required if --area is not specified.
 - --area [NTT_EAST|NTT_WEST]: Use hardcoded DNS servers. Required if --dns-from-dhcpv6 is not specified.
 - --insecure [true]: Optional. Do not check TLS certificate.
 - --debug [true]: Optional. Output debug messages.
 - --ipip-ifl [Interface Name(IFL)]: Optional. Specify IP-IP tunnel interface for DS-Lite tunnel.

## Verified VNEs
 - Internet Multifeed transix (NTT East, Flet's Next, 2022/02)
   - AFTR address is an IPv6 address.
 - AsahiNet v6コネクト (NTT East, Flet's Cross, 2022/02)
   - AFTR address is FQDN. Returns 1 AAAA record.

## Caveats
 - Covers only vendorid, product, version and capability parameters. Persistent token and authentication is not implemented.
 - Access sequence is a bit different from the specification (c.2 and c.3 is not implemented, wait 10-30 minutes even if failed with the errors.).
 - Currently, SRX doesn't support IPIP6 tunnel. This script works only on MX series router.
 - Currently, MX series router doesn't support DHCPv6 client with autoconfig(RA) mode(statefull ia-pd only).

