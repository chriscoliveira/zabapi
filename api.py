#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import json
import re
import sys
from zabbix_api import ZabbixAPI
import pandas as pd

# faz a conexao com o zabbix
zapi = ZabbixAPI(server="http://192.168.0.172:8080")
zapi.login(user="Admin", password="zabbix")

def get_hostgroups():
    hostgroups = zapi.hostgroup.get({"output": "extend"})
    listaGrupos = []
    for x in hostgroups:
        # texto+=x['name'])
        listaGrupos += [x['name']]
    return listaGrupos

def get_hostgroups_id(grupo):
    groupId = zapi.hostgroup.get({"output": "extend","filter":{"name":grupo}})[0]['groupid']
    return groupId

def gethostsByGroup(grupo):
    hosts_grupo = zapi.host.get({"groupids":get_hostgroups_id(grupo),"output":["host"]})
    listaHosts = []
    for x in hosts_grupo:
        # texto+=x['host'])
        listaHosts += [x['host']]
    return listaHosts

def get_hostid(host):
    hostId = zapi.host.get({"output":"hostid","filter":{"host":host}})[0]['hostid']
    return hostId

def getInfoByHost(host=False,host_id=False,exato=False):
    texto=''
    listacsv='STATUS;HOSTID;HOST;NAME;DESCRICAO;AGENT;SNMP;IPMI;JMX;TEMPLATE;GRUPO\n'
    if exato:
        if host:
            info = zapi.host.get({
                "output":"extend",
                "filter":{"name":host},
                'sortfield': 'name'
            })
        elif host_id:
            info = zapi.host.get({
                "output":"extend",
                "filter":{"hostid":host_id},
                'sortfield': 'name'
            })
        
    else:
        if host:
            info = zapi.host.get({
                "output":"extend",
                'search': {'name': host},
                'sortfield': 'name'
            })
        elif host_id:
            info = zapi.host.get({
                "output":"extend",
                "filter":{"hostid":host_id},
                'sortfield': 'name'
            })
    
    for i in info:
        # print(i)
        if str(host_id).lower() in str(i["hostid"]).lower() or str(host).lower() in str(i["host"]).lower() :
            if i['status'] =="0": status="Ativo" 
            else: status="Inativo"

            texto+=f"Status= {status}\nHostid= {i['hostid']}\nHost= {i['host']}\nName= {i['name']}\nDescription= {i['description']}\n"
            listacsv +=f"{status};{i['hostid']};{i['host']};{i['name']};{i['description']}"
            interfaces = zapi.hostinterface.get({
                'output': 'extend',
                'hostids': i['hostid']
            })
            
            tipos_encontrados = {"1": False, "2": False, "3": False, "4": False}
            texto+="Interfaces Associadas:\n"
            for interface in interfaces:
                
                # Acessa os valores com um fallback para "" caso a chave não exista
                ip = interface.get('ip', "")
                dns = interface.get('dns', "")
                port = interface.get('port', "")
                
                if interface["type"] == "1":
                    texto+=f"\tAgent: IP= {interface['ip']} DNS= {interface['dns']} PORTA= {interface['port']}\n"
                    listacsv+=f";[{interface['ip']},{interface['dns']},{interface['port']}]"  
                    tipos_encontrados["1"] = True

                if interface["type"] == "2":
                    texto+=f"\tSNMP:  IP= {interface['ip']} DNS= {interface['dns']} PORTA= {interface['port']}\n"
                    listacsv+=f";[{interface['ip']},{interface['dns']},{interface['port']}]"
                    tipos_encontrados["2"] = True
                
                if interface["type"] == "3":
                    texto+=f"\tIPMI:  IP= {interface['ip']} DNS= {interface['dns']} PORTA= {interface['port']}\n"
                    listacsv+=f";[{interface['ip']},{interface['dns']},{interface['port']}]"
                    tipos_encontrados["3"] = True
                
                if interface["type"] == "4":
                    texto+=f"\tJMX:   IP= {interface['ip']} DNS= {interface['dns']} PORTA= {interface['port']}\n"
                    listacsv+=f";[{interface['ip']},{interface['dns']},{interface['port']}]"
                    tipos_encontrados["4"] = True
                # Para os tipos não encontrados, adiciona uma entrada vazia
                
            if not tipos_encontrados["1"]:
                texto += "\tAgent: IP=  DNS=  PORTA= \n"
                listacsv += ";["","",""]"

            if not tipos_encontrados["2"]:
                texto += "\tSNMP:  IP=  DNS=  PORTA= \n"
                listacsv += ";["","",""]"

            if not tipos_encontrados["3"]:
                texto += "\tIPMI:  IP=  DNS=  PORTA= \n"
                listacsv += ";["","",""]"

            if not tipos_encontrados["4"]:
                texto += "\tJMX:   IP=  DNS=  PORTA= \n"
                listacsv += ";["","",""]"

            templates= zapi.host.get({
                "filter": {"host": i['host']},
                "selectParentTemplates": ["templateid", "name"]
            })
            template = templates[0].get("parentTemplates", [])
            texto+="Templates Associados:\n"
            tt=[]
            for t in template:
                texto+=f"\tid= {t['templateid']}, nome= {t['name']}\n"
                tt.append(f"{t['templateid']},{t['name']}")
            listacsv+=f";{tt}"

            hosts = zapi.host.get({
                'search': {'host': i["host"]},
                'sortfield': 'name',
                
                "selectGroups": ["groupid", "name"]
            })

            groups = hosts[0].get("groups", [])
            texto+="Grupos Associados:\n"
            gg=[]

            if groups:
                group_data = {group["name"]: group["groupid"] for group in groups}
                
                for gr in group_data.items():
                    texto+= f"\tid= {gr[1]}, Grupo= {gr[0]}\n"
                    gg.append(f"{gr[1]},{gr[0]}")
            texto+=f"\n{'-'*60}\n\n"       
            listacsv+=f";{gg}\n"     

    return texto,listacsv

def criaTxt(nome,texto,csv=False):
    with open(nome+".txt","w") as f:
        f.write(f"{texto}")
    if csv:
        with open(nome+".csv","w") as f:
            f.write(f"{listacsv}")

# gruposEncontrados=get_hostgroups()
# idHostGroups=get_hostgroups_id("CT18")
# hosts=gethostsByGroup("CT18")
# hostId=get_hostid("CT18CPD001")

host,listacsv = getInfoByHost(host=False,host_id="10637",exato=False)
criaTxt("host",host,csv=True)


