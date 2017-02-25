#!/usr/bin/python3
import os
import sys
import xml.etree.ElementTree as ET

name_node = sys.argv[1]
core_file = os.environ['HADOOP_HOME']+'/etc/hadoop/core-site.xml'
core_site = ET.parse(core_file)
conf = core_site.getroot()

prop = ET.SubElement(conf,'property')

name = ET.Element('name')
name.text = 'fs.defaultFS'
prop.append(name)

value = ET.Element('value')
value.text = 'hdfs://'+name_node+':8020'
prop.append(value)

core_site.write(core_file)