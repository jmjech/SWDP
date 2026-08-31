# -*- coding: utf-8 -*-
"""
convert_EK-to-netCDF4 

Use echopype to convert Simrad EK60 and EK80 raw files to netCDF4 format

jech
"""

import echopype as ep
from echopype import open_raw
from pathlib import Path, PurePath
import json
from sys import exit
import sys
import argparse
#import utils

    
def main(args):
    # parse the arguments and get the filenames and paths
    pars_dict = utils.parse_args(args, showit=True)
    print(pars_dict['sonar_model'])

    # convert each to netCDF4    
    for f in pars_dict['EK_files']:
        print('Converting: ', f)
        ed = open_raw(str(f), sonar_model=pars_dict['sonar_model'])
        # Henry B. Bigelow ICES code is 33HH
        ed['Platform']['platform_name'] = pars_dict['platform']['name']
        ed['Platform']['platform_type'] = pars_dict['platform']['type']
        ed['Platform']['platform_code_ICES'] = pars_dict['platform']['ICES_code']
        # the to_netcdf function seems to have an error catch, so I don't use "try"
#        ed.to_netcdf(save_path=str(f.parent / pars_dict['nc_dirname']))
    

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Convert EK .raw files to \
        Echopype netCDF4 format')
    parser.add_argument('EKmodel', nargs='?', choices=['EK60', 'EK80'], 
            help='mandatory argument!')
    parser.add_argument('-dd', '--dataDirectory', type=Path, help='data file \
        directory')
    parser.add_argument('-f', '--filenames', type=Path, default=[], nargs='+',
            help='data file name(s) with full path if no data directory is \
            provided: returns a list')
    parser.add_argument('-j', '--jsonfile', type=Path, help='json file full \
        path and file name')
    parser.add_argument('-pn', '--Pname', help='Platform code: name')
    parser.add_argument('-pt', '--Ptype', help='Platform code: type')
    parser.add_argument('-pc', '--Pcode', help='Platform code: ICES code')
    parser.add_argument('-nc', '--ncdirname', type=Path, help='netCDF4 output \
            directory name')
    args = parser.parse_args()

    if (args.EKmodel is None):
        print('Mandatory Argument EKmodel is not Provided! Try the -h option')
        exit()
    elif (args.dataDirectory is None and len(args.filenames) == 0 and args.jsonfile is None):
        print('No files Provided! Try the -h option')
        exit()
    else:
        main(args)

    #if any(vars(args).values()):
    #    main(args)
    #else:
    #    print('No Arguments Provided! Try the -h option')

