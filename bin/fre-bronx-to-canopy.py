#!/home/oar.gfdl.sw/conda/miniconda3/envs/cylc/bin/python
import re
import sys
import xml.etree.ElementTree as ET
import metomi.rose.config

# Usage: fre-bronx-to-canopy -x XML -E EXP
#
# Will overwrite 3 files:
# - rose-suite.conf
# - app/remap-pp-components/rose-app.conf
# - app/regrid-xy/rose-app.conf

def freq_from_legacy(legacy_freq):
    """Return ISO8601 duration given Bronx-style frequencies

    Arguments:
        legacy_freq (str)
"""
    lookup = {
        'annual': 'P1Y',
        'monthly': 'P1M',
        'seasonal': 'P3M',
        'daily': 'P1D',
        '120hr': 'P120D',
        '12hr': 'PT12H',
        '8hr': 'PT8H',
        '6hr': 'PT6H',
        '4hr': 'PT4H',
        '3hr': 'PT3H',
        '2hr': 'PT2H',
        '1hr': 'PT1H',
        '30min': 'PT30M' }
    return lookup[legacy_freq]

def chunk_from_legacy(legacy_chunk):
    """Return ISO8601 duration given Bronx-style chunk

    Arguments:
        legacy_chunk (str)
"""
    regex = re.compile('(\d+)(\w+)')
    match = regex.match(legacy_chunk)
    assert match
    if match.group(2) == "yr":
        return 'P{}Y'.format(match.group(1))
    elif match.group(2) == 'mo':
        return 'P{}M'.format(match.group(1))
    else:
        raise Exception('Unknown time units', match.group(2))



#xml = '/home/Sergey.Malyshev/ncrc/lm4p2/xanadu/lm4p2-am4p0pi.xml'
xml = 'lm4p2-am4p0pi.xml'
expname = 'lm4p2-am4p0pi'

# input
tree = ET.parse(xml)
root = tree.getroot()

# output
rose_remap = metomi.rose.config.ConfigNode()
rose_remap.set(keys=['command', 'default'], value='remap-pp-components')

regex_fre_property = re.compile('\$\((\w+)')






# read XML
print("Parsing XML...")
for exp in root.iter('experiment'):
    if exp.get('name') == expname:
        pp = exp.find('postProcess')
        for comp in exp.iter('component'):
            type = comp.get('type')
            print("Processing component", type)
            i = 1
            if comp.get('xyInterp'):
                grid = "regrid-xy"
            else:
                grid = "native"
            comp_source = comp.get('source')
            sources = set()
            for ts in comp.iter('timeSeries'):
                print("  Timeseries", i)
                if i == 1:
                    label = type
                    print("    ", type)
                else:
                    label = type . i
                    print("    ", type, i)
                source = ts.get('source')
                if source:
                    print("    ", source)
                    s = source
                    sources.add(source)
                else:
                    print("    ", comp_source)
                    s = comp_source
                    sources.add(comp_source)
                rose_remap.set(keys=[label, 'source'], value=s)
                freq = ts.get('freq')
                print("    ", freq)
                rose_remap.set(keys=[label, 'freq'], value=freq)
                chunk = ts.get('chunkLength')
                rose_remap.set(keys=[label, 'chunk'], value=chunk)
                rose_remap.set(keys=[label, 'grid'], value=grid)
                print("    ", chunk)
                print("    ", grid)

            print("  Statics")
            print("    ", type, ".static")
            print("    ", ", ".join(sources))

            if grid == "native":
                print("  No regridding")
                continue
            else:
                print("  Regridding info")
                print("    ", type)
                print("    ", ", ".join(sources))
                interp = comp.get('xyInterp')
                print("    ", interp)
                sourcegrid = comp.get('sourceGrid')
                print("    ", sourcegrid)
            ++i





print("Looking up FRE properties...")
properties = dict()

for keys, sub_node in rose_remap.walk():
    if len(keys) != 1:
        continue
    item = keys[0]
    if item == "env" or item == "command":
        continue
    value = rose_remap.get_value(keys=[item, 'chunk'])
    match = regex_fre_property.match(value)
    if not match:
        pass
    else:
        name = match.group(1)
        if name in properties:
            pass
        else:
            string = './property[@name="{}"]'.format(name)
            results = root.findall(string)
            assert len(results) == 1
            properties[name] = results[0].get('value')
            print("  {}: {}".format(name, properties[name]))
        rose_remap = rose_remap.set([item, 'chunk'], properties[name])


print("Converting Bronx date info to ISO8601...")
freq_from_legacy('annual')

for keys, sub_node in rose_remap.walk():
    if len(keys) != 1:
        continue
    item = keys[0]
    if item == "env" or item == "command":
        continue
    freq_legacy = rose_remap.get_value(keys=[item, 'freq'])
    rose_remap.set([item, 'freq'], freq_from_legacy(freq_legacy))
    chunk_legacy = rose_remap.get_value(keys=[item, 'chunk'])
    rose_remap.set([item, 'chunk'], chunk_from_legacy(chunk_legacy))


print("Writing output files...")
dumper = metomi.rose.config.ConfigDumper()

outfile = "app/remap-pp-components/rose-app.conf"
print("  Writing", outfile)
dumper(rose_remap, outfile)
